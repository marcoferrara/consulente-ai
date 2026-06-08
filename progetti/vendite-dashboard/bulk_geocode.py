import csv
import json
import os
import urllib.request
import urllib.parse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import re

base_dir = os.path.dirname(os.path.abspath(__file__))
csv_input_path = os.path.join(base_dir, 'Vendite_Soggetti.csv')
cache_path = os.path.join(base_dir, 'geocoding_cache.json')
json_output_path = os.path.join(base_dir, 'src/data/clients_data.json')


def is_in_sardinia(lat, lon):
    # Bounding box for Sardinia
    return 38.8 <= lat <= 41.5 and 8.0 <= lon <= 10.0

# Load cache if exists
cache = {}
# We will discard the previous cache because it contains incorrect coordinates outside Sardinia.
# Let's delete the cache or force re-geocoding for points outside Sardinia.
if os.path.exists(cache_path):
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            temp_cache = json.load(f)
        for addr, coords in temp_cache.items():
            if coords and len(coords) == 2 and coords[0] != "" and coords[1] != "":
                lat = float(coords[0])
                lon = float(coords[1])
                if is_in_sardinia(lat, lon):
                    cache[addr] = (lat, lon)
        print(f"Loaded {len(cache)} valid Sardinia geocoded items from cache.")
    except Exception as e:
        print(f"Error loading cache: {e}")

# Read subjects CSV
leads = []
with open(csv_input_path, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        leads.append(row)

print(f"Total leads in CSV: {len(leads)}")

lock = threading.Lock()
cache_dirty = False

def save_cache():
    global cache_dirty
    with lock:
        if cache_dirty:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            cache_dirty = False

def query_photon(address):
    # Restrict to Sardinia, Italy
    query_str = address
    if "sardinia" not in query_str.lower():
        query_str = f"{address}, Sardinia, Italy"
        
    url = f"https://photon.komoot.io/api/?q={urllib.parse.quote(query_str)}&limit=1"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('features'):
                geom = data['features'][0]['geometry']
                coords = geom['coordinates'] # [lon, lat]
                lat, lon = coords[1], coords[0]
                if is_in_sardinia(lat, lon):
                    return lat, lon
    except Exception:
        pass
    return None

def re_clean_street(addr_str):
    m = urllib.parse.unquote(addr_str)
    match = re.search(r'\d{5}', m)
    if match:
        return m[:match.start()].strip()
    return addr_str

def geocode_address(address, city, zip_code, province):
    if address in cache:
        return cache[address]
        
    time.sleep(0.15) # Polite delay
    
    # Try 1: Full Address
    coords = query_photon(address)
    if coords:
        return coords
        
    # Try 2: Clean Street + City
    street_clean = re_clean_street(address)
    if street_clean and city:
        coords = query_photon(f"{street_clean}, {city}")
        if coords:
            return coords

    # Try 3: City + ZIP + Province
    if city:
        coords = query_photon(f"{city} {zip_code} {province}")
        if coords:
            return coords
            
    # Try 4: City + Province
    if city:
        coords = query_photon(f"{city} {province}")
        if coords:
            return coords

    # Try 5: Just City
    if city:
        coords = query_photon(city)
        if coords:
            return coords

    # Try 6: Just Province
    if province:
        coords = query_photon(province)
        if coords:
            return coords

    return "", ""

# Identify addresses that need geocoding
to_geocode = []
for item in leads:
    addr = item['Indirizzo']
    lat = item['Latitudine']
    lon = item['Longitudine']
    
    # Check if we already have coordinates in the KML
    if lat and lon:
        with lock:
            cache[addr] = (float(lat), float(lon))
        continue
        
    if addr and addr not in cache:
        to_geocode.append(item)

print(f"Items needing geocoding: {len(to_geocode)}")

# Geocode in parallel
completed_count = 0
total_to_geocode = len(to_geocode)

def process_item(item):
    global completed_count, cache_dirty
    addr = item['Indirizzo']
    city = item['Comune']
    zip_code = item['CAP']
    prov = item['Provincia']
    
    lat, lon = geocode_address(addr, city, zip_code, prov)
    
    with lock:
        cache[addr] = (lat, lon)
        cache_dirty = True
        completed_count += 1
        if completed_count % 50 == 0 or completed_count == total_to_geocode:
            print(f"Progress: {completed_count}/{total_to_geocode} geocoded...")
            
    # Save cache incrementally
    if completed_count % 100 == 0:
        save_cache()

if to_geocode:
    print("Starting geocoding using 5 threads...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_item, item): item for item in to_geocode}
        for future in as_completed(futures):
            future.result()
            
    save_cache()
    print("Geocoding completed and cache saved.")
else:
    print("No items need geocoding.")

# Compile final dataset
final_leads = []
for item in leads:
    addr = item['Indirizzo']
    lat, lon = cache.get(addr, ("", ""))
    
    # Check what sector
    name = item['Nome'].lower()
    category = 'Altro'
    categories_map = {
        'Trasporti e Logistica': r'trasporti|logistica|autotrasporti|trasp|logistic|spedizion',
        'Automotive e Officine': r'ricambi|autoricambi|car service|officina|meccanica|carrozzeria|gomme|auto|veicoli|truck',
        'Edilizia e Costruzioni': r'edil|costruzioni|beton|marmi|scavi|cement|inerti',
        'Servizi e Cooperative': r'cooperativa|società coop|consorzio|servizi|service|soccorso',
        'Agricoltura e Floricoltura': r'agricola|agri|flor|orto|agriturismo|allevamento|vigne|cantin',
        'Alimentari e Ristorazione': r'carni|alimentari|ristorante|pizzeria|bar|caffè|market|panific|salum|caseific'
    }
    
    for cat_name, pattern in categories_map.items():
        if re.search(pattern, name):
            category = cat_name
            break
            
    final_leads.append({
        'name': item['Nome'],
        'address': item['Indirizzo'],
        'street': item['Via'],
        'zip': item['CAP'],
        'city': item['Comune'] if item['Comune'] else "Sconosciuto",
        'province': item['Provincia'],
        'lat': float(lat) if lat != "" else None,
        'lng': float(lon) if lon != "" else None,
        'category': category
    })

# Save JSON file
with open(json_output_path, 'w', encoding='utf-8') as f:
    json.dump(final_leads, f, ensure_ascii=False, indent=2)

print(f"Saved {len(final_leads)} items to JSON: {json_output_path}")
