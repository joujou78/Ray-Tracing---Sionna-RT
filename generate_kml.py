import re

# ======================== CONFIGURATION ========================
INPUT_FILE  = r'C:\Users\Bahjat\Downloads\nottingham915.csv'
OUTPUT_KML  = 'rx_tx_points_915.kml'
MAX_POINTS  = None   # set to 1200 to limit to first 1200 RX, None = all
# ===============================================================


def rssi_to_color(rssi, min_rssi, max_rssi):
    """Map RSSI → KML color (aabbggrr): green=strong, red=weak."""
    t = max(0.0, min(1.0, (rssi - min_rssi) / (max_rssi - min_rssi))) if max_rssi > min_rssi else 0.5
    r = int((1.0 - t) * 255)
    g = int(t * 255)
    return f'ff{0:02x}{g:02x}{r:02x}'


def parse_header_and_data(filename):
    tx_lat = tx_lon = None
    rx_points = []

    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines[:30]:
        if 'Site latitude' in line:
            m = re.search(r'([-+]?\d+\.\d+)', line)
            if m: tx_lat = float(m.group(1))
        elif 'Site longitude' in line:
            m = re.search(r'([-+]?\d+\.\d+)', line)
            if m: tx_lon = float(m.group(1))
        if tx_lat and tx_lon:
            break

    data_start = 0
    for i, line in enumerate(lines):
        if 'Date' in line and 'Rx Latitude' in line and 'Rx Longitude' in line:
            data_start = i + 1
            break

    for line in lines[data_start:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(',')
        if len(parts) < 5:
            continue
        try:
            rx_points.append((float(parts[2]), float(parts[3]), float(parts[4])))
        except ValueError:
            continue

    return (tx_lat, tx_lon), rx_points


def generate_kml(tx_coords, rx_points, output_file):
    if MAX_POINTS:
        rx_points = rx_points[:MAX_POINTS]

    rssi_vals = [m for _, _, m in rx_points]
    min_r, max_r = min(rssi_vals), max(rssi_vals)

    N_BUCKETS = 50
    bucket_styles = ''
    for b in range(N_BUCKETS + 1):
        rssi_b = min_r + (max_r - min_r) * b / N_BUCKETS
        color  = rssi_to_color(rssi_b, min_r, max_r)
        bucket_styles += f'''
    <Style id="rssi_{b}">
        <IconStyle>
            <color>{color}</color>
            <scale>0.7</scale>
            <Icon><href>http://maps.google.com/mapfiles/kml/shapes/circle.png</href></Icon>
        </IconStyle>
        <LabelStyle><scale>0</scale></LabelStyle>
    </Style>'''

    kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <name>Nottingham 915 MHz — RSSI map</name>
    <description>RSSI range: {min_r:.1f} dBm (red) to {max_r:.1f} dBm (green)</description>

    <Style id="txStyle">
        <IconStyle>
            <color>ff0000ff</color><scale>1.4</scale>
            <Icon><href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href></Icon>
        </IconStyle>
        <LabelStyle><scale>1.0</scale></LabelStyle>
    </Style>
{bucket_styles}
'''

    if tx_coords[0]:
        kml += f'''
    <Placemark>
        <name>TX</name>
        <description>Transmitter | lat={tx_coords[0]} lon={tx_coords[1]}</description>
        <styleUrl>#txStyle</styleUrl>
        <Point><coordinates>{tx_coords[1]},{tx_coords[0]},0</coordinates></Point>
    </Placemark>
'''

    for i, (lat, lon, rssi) in enumerate(rx_points, start=1):
        rx_id  = f'RX_{i:06d}'
        bucket = int(round((rssi - min_r) / (max_r - min_r) * N_BUCKETS)) if max_r > min_r else 0
        bucket = max(0, min(N_BUCKETS, bucket))
        kml += f'''
    <Placemark>
        <name>{rx_id}</name>
        <description>ID: {rx_id} | RSSI: {rssi:.2f} dBm</description>
        <styleUrl>#rssi_{bucket}</styleUrl>
        <Point><coordinates>{lon},{lat},0</coordinates></Point>
    </Placemark>
'''

    kml += '</Document>\n</kml>\n'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(kml)
    print(f"KML saved : {output_file}")
    print(f"RX points : {len(rx_points)}")
    print(f"RSSI range: {min_r:.1f} dBm (red) -> {max_r:.1f} dBm (green)")


if __name__ == '__main__':
    tx, rx_points = parse_header_and_data(INPUT_FILE)
    print(f"TX        : {tx}")
    print(f"RX count  : {len(rx_points)}")
    generate_kml(tx, rx_points, OUTPUT_KML)
