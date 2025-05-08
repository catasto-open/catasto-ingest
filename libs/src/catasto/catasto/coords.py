import math
from typing import List, Optional, Tuple

import pyproj
import structlog


class CRS:
    """Gestione dei sistemi di riferimento per le coordinate catastali."""

    # Sistemi di riferimento catastali italiani
    # I parametri sono definiti in base alle specifiche dell'Agenzia del Territorio
    CASSINI_SOLDNER_ORIGINS = {
        # Codice comune: (Monte Mario Long, Monte Mario Lat, meridiano centrale, shift X, shift Y)
        # Questi sono esempi, i parametri reali variano per ogni comune
        "H501": (
            12.452128847598,
            41.924403024984,
            12.452128847598,
            0,
            0,
        ),  # Roma, vedere grandi origini
        "A944": (8.6142, 45.8665, 8.6142, 0, 0),  # Bologna, da validare
        "F205": (9.1895, 45.4642, 9.1895, 0, 0),  # Milano, da validare
        # Aggiungere altri comuni secondo necessità
    }

    # Limiti tipici delle coordinate Cassini-Soldner
    # Questi valori possono variare in base all'implementazione specifica
    CASSINI_SOLDNER_RANGE = {
        "x_min": -50000,  # metri
        "x_max": 50000,
        "y_min": -50000,
        "y_max": 50000,
    }

    # Limiti tipici delle coordinate Gauss-Boaga
    GAUSS_BOAGA_RANGE = {
        "x_min": 1400000,  # metri (Fuso Ovest)
        "x_max": 2700000,  # metri (Fuso Est)
        "y_min": 3900000,
        "y_max": 5200000,
    }

    def __init__(self, logger=None):
        """
        Inizializza l'utilità per la gestione delle coordinate catastali.

        Args:
            logger: Logger strutturato da utilizzare
        """
        self.logger = logger or structlog.get_logger("catasto.coords")

        # Inizializza i trasformatori di coordinate
        self._init_transformers()

    def _init_transformers(self):
        """Inizializza i trasformatori per i sistemi di coordinate supportati."""
        # WGS84 (EPSG:4326)
        self.wgs84 = pyproj.CRS.from_epsg(4326)

        # Monte Mario / Italy zone 1 - Gauss-Boaga Fuso Ovest (EPSG:3003)
        self.gauss_boaga_west = pyproj.CRS.from_epsg(3003)

        # Monte Mario / Italy zone 2 - Gauss-Boaga Fuso Est (EPSG:3004)
        self.gauss_boaga_east = pyproj.CRS.from_epsg(3004)

        # Trasformatori predefiniti
        self.gb_west_to_wgs84 = pyproj.Transformer.from_crs(
            self.gauss_boaga_west, self.wgs84, always_xy=True
        )
        self.gb_east_to_wgs84 = pyproj.Transformer.from_crs(
            self.gauss_boaga_east, self.wgs84, always_xy=True
        )
        self.wgs84_to_gb_west = pyproj.Transformer.from_crs(
            self.wgs84, self.gauss_boaga_west, always_xy=True
        )
        self.wgs84_to_gb_east = pyproj.Transformer.from_crs(
            self.wgs84, self.gauss_boaga_east, always_xy=True
        )

    def detect_coordinate_system(self, coordinates: List[Tuple], mun_code: str) -> str:
        """
        Rileva il probabile sistema di coordinate usato nel file CXF.

        Args:
            coordinates: Lista di coordinate (x, y) che possono essere float o stringhe
            mun_code: Codice del comune

        Returns:
            str: Il sistema di coordinate rilevato ('cassini-soldner', 'gauss-boaga-west', 'gauss-boaga-east', 'unknown')
        """
        # Verifica se è un comune con coordinate Cassini-Soldner note
        if mun_code in self.CASSINI_SOLDNER_ORIGINS:
            self.logger.info(f"Il comune {mun_code} è noto per usare Cassini-Soldner")

        # Converte le coordinate in float se sono stringhe
        numeric_coordinates = []
        for coord in coordinates:
            try:
                if isinstance(coord[0], str) or isinstance(coord[1], str):
                    x = float(coord[0])
                    y = float(coord[1])
                    numeric_coordinates.append((x, y))
                else:
                    numeric_coordinates.append(coord)
            except (ValueError, TypeError, IndexError):
                # Ignora le coordinate che non possono essere convertite
                continue

        if not numeric_coordinates:
            return "unknown"

        # Verifica il range delle coordinate
        x_values = [coord[0] for coord in numeric_coordinates]
        y_values = [coord[1] for coord in numeric_coordinates]

        if not x_values or not y_values:
            return "unknown"

        min_x = min(x_values)
        max_x = max(x_values)
        min_y = min(y_values)
        max_y = max(y_values)

        self.logger.debug(
            f"Range coordinate: X={min_x:.2f} to {max_x:.2f}, Y={min_y:.2f} to {max_y:.2f}"
        )

        # Verifica se rientra nel range Gauss-Boaga
        if (
            min_x >= self.GAUSS_BOAGA_RANGE["x_min"]
            and max_x <= self.GAUSS_BOAGA_RANGE["x_max"]
            and min_y >= self.GAUSS_BOAGA_RANGE["y_min"]
            and max_y <= self.GAUSS_BOAGA_RANGE["y_max"]
        ):
            # Determina se Fuso Est o Ovest
            if max_x < 1800000:  # Soglia approssimativa tra i due fusi
                return "gauss-boaga-west"
            else:
                return "gauss-boaga-east"

        # Verifica range Cassini-Soldner locale
        if (
            abs(min_x) <= abs(self.CASSINI_SOLDNER_RANGE["x_max"])
            and abs(max_x) <= abs(self.CASSINI_SOLDNER_RANGE["x_max"])
            and abs(min_y) <= abs(self.CASSINI_SOLDNER_RANGE["y_max"])
            and abs(max_y) <= abs(self.CASSINI_SOLDNER_RANGE["y_max"])
        ):
            return "cassini-soldner"

        return "unknown"

    def create_cassini_soldner_crs(self, mun_code: str) -> Optional[pyproj.CRS]:
        """
        Crea un sistema di riferimento Cassini-Soldner per un comune specifico.

        Args:
            mun_code: Codice del comune

        Returns:
            pyproj.CRS: Oggetto CRS per Cassini-Soldner
        """
        if mun_code not in self.CASSINI_SOLDNER_ORIGINS:
            self.logger.warning(
                f"Parametri Cassini-Soldner non disponibili per il comune {mun_code}"
            )
            return None

        # Recupera i parametri per il comune
        mm_lon, mm_lat, central_meridian, shift_x, shift_y = (
            self.CASSINI_SOLDNER_ORIGINS[mun_code]
        )

        # Definisci il sistema Cassini-Soldner utilizzando PROJ string
        proj_string = (
            f"+proj=cass +lat_0={mm_lat} +lon_0={central_meridian} "
            f"+x_0={shift_x} +y_0={shift_y} +ellps=intl +units=m +no_defs"
        )

        try:
            cassini_soldner_crs = pyproj.CRS.from_string(proj_string)
            return cassini_soldner_crs
        except Exception as e:
            self.logger.error(
                f"Errore nella creazione del CRS Cassini-Soldner: {str(e)}"
            )
            return None

    def transform_coordinates(
        self,
        coordinates: List[Tuple[float, float]],
        source_crs: str,
        target_crs: str = "gauss-boaga-west",
        mun_code: str = None,
    ) -> List[Tuple[float, float]]:
        """
        Trasforma le coordinate da un sistema all'altro.

        Args:
            coordinates: Lista di coordinate (x, y)
            source_crs: Sistema di coordinate sorgente ('cassini-soldner', 'gauss-boaga-west', 'gauss-boaga-east', 'wgs84')
            target_crs: Sistema di coordinate target ('gauss-boaga-west', 'gauss-boaga-east', 'wgs84')
            mun_code: Codice del comune (necessario per Cassini-Soldner)

        Returns:
            List[Tuple[float, float]]: Lista di coordinate trasformate
        """
        if not coordinates:
            return []

        # Se sorgente e target sono uguali, restituisci le coordinate originali
        if source_crs == target_crs:
            return coordinates

        # Per trasformazioni da/a Cassini-Soldner, è necessario il codice comune
        if (
            source_crs == "cassini-soldner" or target_crs == "cassini-soldner"
        ) and not mun_code:
            self.logger.error(
                "Codice comune necessario per trasformazioni con Cassini-Soldner"
            )
            return coordinates

        try:
            # Crea trasformatore appropriato
            if source_crs == "cassini-soldner":
                # Da Cassini-Soldner passiamo prima a WGS84 e poi al target
                cassini_crs = self.create_cassini_soldner_crs(mun_code)
                if not cassini_crs:
                    return coordinates

                # Cassini-Soldner -> WGS84
                transformer_to_wgs84 = pyproj.Transformer.from_crs(
                    cassini_crs, self.wgs84, always_xy=True
                )

                # Trasforma prima in WGS84
                wgs84_coords = [
                    transformer_to_wgs84.transform(x, y) for x, y in coordinates
                ]

                # Poi da WGS84 al target
                if target_crs == "wgs84":
                    return wgs84_coords
                elif target_crs == "gauss-boaga-west":
                    return [
                        self.wgs84_to_gb_west.transform(lon, lat)
                        for lon, lat in wgs84_coords
                    ]
                elif target_crs == "gauss-boaga-east":
                    return [
                        self.wgs84_to_gb_east.transform(lon, lat)
                        for lon, lat in wgs84_coords
                    ]

            elif target_crs == "cassini-soldner":
                # Prima trasformiamo in WGS84
                wgs84_coords = []
                if source_crs == "gauss-boaga-west":
                    wgs84_coords = [
                        self.gb_west_to_wgs84.transform(x, y) for x, y in coordinates
                    ]
                elif source_crs == "gauss-boaga-east":
                    wgs84_coords = [
                        self.gb_east_to_wgs84.transform(x, y) for x, y in coordinates
                    ]
                elif source_crs == "wgs84":
                    wgs84_coords = coordinates

                # Poi da WGS84 a Cassini-Soldner
                cassini_crs = self.create_cassini_soldner_crs(mun_code)
                if not cassini_crs:
                    return coordinates

                transformer_from_wgs84 = pyproj.Transformer.from_crs(
                    self.wgs84, cassini_crs, always_xy=True
                )
                return [
                    transformer_from_wgs84.transform(lon, lat)
                    for lon, lat in wgs84_coords
                ]

            else:
                # Trasformazioni tra Gauss-Boaga e WGS84
                if source_crs == "gauss-boaga-west" and target_crs == "wgs84":
                    return [
                        self.gb_west_to_wgs84.transform(x, y) for x, y in coordinates
                    ]
                elif source_crs == "gauss-boaga-east" and target_crs == "wgs84":
                    return [
                        self.gb_east_to_wgs84.transform(x, y) for x, y in coordinates
                    ]
                elif source_crs == "wgs84" and target_crs == "gauss-boaga-west":
                    return [
                        self.wgs84_to_gb_west.transform(lon, lat)
                        for lon, lat in coordinates
                    ]
                elif source_crs == "wgs84" and target_crs == "gauss-boaga-east":
                    return [
                        self.wgs84_to_gb_east.transform(lon, lat)
                        for lon, lat in coordinates
                    ]
                elif (
                    source_crs == "gauss-boaga-west"
                    and target_crs == "gauss-boaga-east"
                ):
                    # Passa per WGS84
                    wgs84_coords = [
                        self.gb_west_to_wgs84.transform(x, y) for x, y in coordinates
                    ]
                    return [
                        self.wgs84_to_gb_east.transform(lon, lat)
                        for lon, lat in wgs84_coords
                    ]
                elif (
                    source_crs == "gauss-boaga-east"
                    and target_crs == "gauss-boaga-west"
                ):
                    # Passa per WGS84
                    wgs84_coords = [
                        self.gb_east_to_wgs84.transform(x, y) for x, y in coordinates
                    ]
                    return [
                        self.wgs84_to_gb_west.transform(lon, lat)
                        for lon, lat in wgs84_coords
                    ]

            self.logger.error(
                f"Combinazione di CRS non supportata: {source_crs} -> {target_crs}"
            )
            return coordinates

        except Exception as e:
            self.logger.error(f"Errore nella trasformazione delle coordinate: {str(e)}")
            return coordinates


# Classe per il calcolo delle trasformazioni delle coordinate Cassini-Soldner
class CassiniSoldnerTransformer:
    """
    Implementazione specializzata delle trasformazioni Cassini-Soldner per il Catasto italiano.
    Basata sulle formule di trasformazione dell'Agenzia del Territorio.
    """

    # Parametri dell'ellissoide Roma40 (Internazionale 1924)
    # Semiasse maggiore in metri
    a = 6378388.0

    # Schiacciamento dell'ellissoide
    f = 1.0 / 297.0

    # Eccentricità derivata
    e_squared = 2 * f - f * f

    def __init__(self, origin_lat, origin_lon, false_easting=0.0, false_northing=0.0):
        """
        Inizializza il trasformatore Cassini-Soldner con i parametri locali.

        Args:
            origin_lat: Latitudine dell'origine in gradi decimali
            origin_lon: Longitudine dell'origine in gradi decimali
            false_easting: Falsa origine Est (in metri)
            false_northing: Falsa origine Nord (in metri)
        """
        # Converti in radianti
        self.phi0 = math.radians(origin_lat)
        self.lambda0 = math.radians(origin_lon)

        # False origini
        self.FE = false_easting
        self.FN = false_northing

        # Calcola le costanti
        self._compute_constants()

    def _compute_constants(self):
        """Calcola le costanti utilizzate nelle formule di trasformazione."""
        # Calcola il raggio di curvatura meridiana all'origine
        self.M0 = (
            self.a
            * (1 - self.e_squared)
            / (1 - self.e_squared * math.sin(self.phi0) ** 2) ** 1.5
        )

        # Calcola il raggio di curvatura primo verticale all'origine
        self.N0 = self.a / math.sqrt(1 - self.e_squared * math.sin(self.phi0) ** 2)

    def geo_to_cassini(self, lat, lon):
        """
        Converte coordinate geografiche (WGS84) in coordinate Cassini-Soldner.

        Args:
            lat: Latitudine in gradi decimali
            lon: Longitudine in gradi decimali

        Returns:
            tuple: Coordinate (x, y) in metri nel sistema Cassini-Soldner
        """
        # Converti in radianti
        phi = math.radians(lat)
        lambda_ = math.radians(lon)

        # Differenza di longitudine
        delta_lambda = lambda_ - self.lambda0

        # Calcolo del raggio di curvatura meridiana
        M = (
            self.a
            * (1 - self.e_squared)
            / (1 - self.e_squared * math.sin(phi) ** 2) ** 1.5
        )

        # Calcolo del raggio di curvatura primo verticale
        N = self.a / math.sqrt(1 - self.e_squared * math.sin(phi) ** 2)

        # Calcolo delle coordinate
        x = N * math.cos(phi) * math.sin(delta_lambda) + self.FE

        # Formula approssimata per la coordinata y
        y = (
            M * (phi - self.phi0)
            + 0.5 * N * math.sin(phi) * math.cos(phi) * delta_lambda**2
            + self.FN
        )

        return x, y

    def cassini_to_geo(self, x, y):
        """
        Converte coordinate Cassini-Soldner in coordinate geografiche (WGS84).

        Args:
            x: Coordinata Est in metri
            y: Coordinata Nord in metri

        Returns:
            tuple: Coordinate (lat, lon) in gradi decimali
        """
        # Rimuovi false origini
        x -= self.FE
        y -= self.FN

        # Calcolo approssimato della latitudine
        phi = self.phi0 + y / self.M0

        # Calcola un nuovo valore di M per la latitudine approssimata
        M = (
            self.a
            * (1 - self.e_squared)
            / (1 - self.e_squared * math.sin(phi) ** 2) ** 1.5
        )

        # Calcola N per la latitudine approssimata
        N = self.a / math.sqrt(1 - self.e_squared * math.sin(phi) ** 2)

        # Raffina il calcolo della latitudine con un metodo iterativo
        for _ in range(5):  # Di solito bastano poche iterazioni
            phi = self.phi0 + (y - (N * math.tan(phi) * x**2) / (2 * self.M0**2)) / M
            M = (
                self.a
                * (1 - self.e_squared)
                / (1 - self.e_squared * math.sin(phi) ** 2) ** 1.5
            )
            N = self.a / math.sqrt(1 - self.e_squared * math.sin(phi) ** 2)

        # Calcolo della longitudine
        delta_lambda = math.atan(x / (N * math.cos(phi)))
        lambda_ = self.lambda0 + delta_lambda

        # Converti in gradi
        lat = math.degrees(phi)
        lon = math.degrees(lambda_)

        return lat, lon


def detect_crs_from_cxf(vertices: List[Tuple], mun_code: str) -> str:
    """
    Rileva il sistema di riferimento utilizzato in un file CXF in base alle coordinate dei vertici.

    Args:
        vertices: Lista di tuple con le coordinate dei vertici (x, y) che possono essere float o stringhe
        mun_code: Codice del comune

    Returns:
        str: Sistema di riferimento rilevato ('cassini-soldner', 'gauss-boaga-west', 'gauss-boaga-east', 'unknown')
    """
    crs_util = CRS()
    return crs_util.detect_coordinate_system(vertices, mun_code)


def transform_cxf_vertices(
    vertices: List[Tuple],
    source_crs: str,
    target_crs: str,
    mun_code: str,
) -> List[Tuple]:
    """
    Trasforma le coordinate dei vertici da un sistema di riferimento a un altro,
    mantenendo lo stesso formato dell'input (stringhe o float).

    Args:
        vertices: Lista di tuple con le coordinate dei vertici (x, y) che possono essere float o stringhe
        source_crs: Sistema di riferimento sorgente
        target_crs: Sistema di riferimento target
        mun_code: Codice del comune

    Returns:
        List[Tuple]: Lista di coordinate trasformate nello stesso formato dell'input
    """
    # Determina se l'input è in formato stringa
    is_string_format = False
    if vertices and (
        isinstance(vertices[0][0], str) or isinstance(vertices[0][1], str)
    ):
        is_string_format = True

    # Converte le coordinate in float se sono stringhe
    numeric_vertices = []
    for vertex in vertices:
        try:
            if isinstance(vertex[0], str) or isinstance(vertex[1], str):
                x = float(vertex[0])
                y = float(vertex[1])
                numeric_vertices.append((x, y))
            else:
                numeric_vertices.append(vertex)
        except (ValueError, TypeError, IndexError):
            # Ignora le coordinate che non possono essere convertite
            continue

    # Esegue la trasformazione
    crs_util = CRS()
    transformed_coords = crs_util.transform_coordinates(
        numeric_vertices, source_crs, target_crs, mun_code
    )

    # Converte il risultato nello stesso formato dell'input
    if is_string_format:
        return [(str(x), str(y)) for x, y in transformed_coords]
    else:
        return transformed_coords
