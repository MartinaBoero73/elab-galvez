import re

# HEADER RULES (CA... Files )
# Matches all text on the left, 2 or more spaces, and the label on the right.
CABECERA_PATTERN = re.compile(r'^(.*?)\s{2,}(.+)$')

# DETAIL RULES (DE... Files)
# Captures the monetary amount located at the end of each line ( NOW supports negatives).
MONTO_DETALLE_PATTERN = re.compile(r'(-?[\d.,]+)$')

# Visual indentation thresholds to classify concepts by type.
LIMITE_REMUNERATIVO = 55
LIMITE_DESCUENTO = 80

# METADATA RULES (Filenames)
# Captures: Group 1 (Employer - 3 digits), Group 2 (Employee - 3 digits)
ARCHIVO_METADATA_PATTERN = re.compile(r'(?i)^(?:CA|DE)(\d{3})(\d{3})\.txt$')