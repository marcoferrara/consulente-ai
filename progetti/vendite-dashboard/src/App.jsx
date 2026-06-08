import React, { useState, useMemo, useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import { Search, MapPin, Briefcase, FileText, Printer, Plus, Trash2, Map, CheckSquare, Layers, Award } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import './App.css';

// We import data safely. If data is not yet fully loaded or empty, fallback to empty array.
import rawClientsData from './data/clients_data.json';

// Simple component to adjust map view dynamically based on search or province
function MapUpdater({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, zoom);
    }
  }, [center, zoom, map]);
  return null;
}

function App() {
  // 1. Data load and preprocessing
  const clients = useMemo(() => {
    return (rawClientsData || []).map((c, index) => ({
      ...c,
      id: c.id || `client-${index}`,
      lat: c.lat ? parseFloat(c.lat) : null,
      lng: c.lng ? parseFloat(c.lng) : null,
    }));
  }, []);

  // 2. State variables
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProvince, setSelectedProvince] = useState('');
  const [selectedComune, setSelectedComune] = useState('');
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [tourList, setTourList] = useState([]);
  const [mapCenter, setMapCenter] = useState([40.0, 9.0]); // Sardinia center
  const [mapZoom, setMapZoom] = useState(8);

  // Load tour list from localStorage on mount
  useEffect(() => {
    const savedTour = localStorage.getItem('visit_tour_list');
    if (savedTour) {
      try {
        setTourList(JSON.parse(savedTour));
      } catch (e) {
        console.error("Error parsing saved tour list:", e);
      }
    }
  }, []);

  // Save tour list to localStorage when changed
  const saveTourList = (newTourList) => {
    setTourList(newTourList);
    localStorage.setItem('visit_tour_list', JSON.stringify(newTourList));
  };

  // 3. Unique values for filters
  const provincesList = useMemo(() => {
    const provs = new Set();
    clients.forEach(c => {
      if (c.province) provs.add(c.province);
    });
    return Array.from(provs).sort();
  }, [clients]);

  const comuniList = useMemo(() => {
    const filtered = selectedProvince 
      ? clients.filter(c => c.province === selectedProvince)
      : clients;
    const coms = new Set();
    filtered.forEach(c => {
      if (c.city) coms.add(c.city);
    });
    return Array.from(coms).sort();
  }, [clients, selectedProvince]);

  const categoriesList = [
    'Trasporti e Logistica',
    'Automotive e Officine',
    'Edilizia e Costruzioni',
    'Servizi e Cooperative',
    'Agricoltura e Floricoltura',
    'Alimentari e Ristorazione',
    'Altro'
  ];

  // 4. Filtering logic
  const filteredClients = useMemo(() => {
    return clients.filter(c => {
      // Search term
      const matchesSearch = searchTerm === '' || 
        c.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
        (c.address && c.address.toLowerCase().includes(searchTerm.toLowerCase()));
      
      // Province
      const matchesProvince = selectedProvince === '' || c.province === selectedProvince;
      
      // Comune
      const matchesComune = selectedComune === '' || c.city === selectedComune;
      
      // Category
      const matchesCategory = selectedCategories.length === 0 || selectedCategories.includes(c.category);
      
      return matchesSearch && matchesProvince && matchesComune && matchesCategory;
    });
  }, [clients, searchTerm, selectedProvince, selectedComune, selectedCategories]);

  // Adjust map viewport based on filters
  useEffect(() => {
    if (selectedComune) {
      // Find first client with coordinates in this Comune
      const clientInComune = filteredClients.find(c => c.city === selectedComune && c.lat && c.lng);
      if (clientInComune) {
        setMapCenter([clientInComune.lat, clientInComune.lng]);
        setMapZoom(13);
      }
    } else if (selectedProvince) {
      // Map province centroids roughly
      const provinceCentroids = {
        'CA': [39.2276, 9.1157],
        'SU': [39.15, 8.65],
        'SS': [40.7259, 8.5602],
        'NU': [40.3204, 9.3283],
        'OR': [39.9056, 8.5919],
        'VS': [39.5606, 8.8584],
        'CI': [39.1678, 8.5222],
        'OT': [40.9242, 9.4975],
        'OG': [39.8732, 9.5447]
      };
      if (provinceCentroids[selectedProvince]) {
        setMapCenter(provinceCentroids[selectedProvince]);
        setMapZoom(9.5);
      }
    } else {
      setMapCenter([40.0, 9.0]);
      setMapZoom(8);
    }
  }, [selectedProvince, selectedComune, filteredClients]);

  // Reset Comune when Province changes
  const handleProvinceChange = (e) => {
    setSelectedProvince(e.target.value);
    setSelectedComune('');
  };

  // Toggle Category selection
  const toggleCategory = (cat) => {
    if (selectedCategories.includes(cat)) {
      setSelectedCategories(selectedCategories.filter(c => c !== cat));
    } else {
      setSelectedCategories([...selectedCategories, cat]);
    }
  };

  // 5. Visit Planner Actions
  const addToTour = (client) => {
    if (!tourList.some(item => item.id === client.id)) {
      const updated = [...tourList, client];
      saveTourList(updated);
    }
  };

  const removeFromTour = (clientId) => {
    const updated = tourList.filter(item => item.id !== clientId);
    saveTourList(updated);
  };

  const clearTour = () => {
    if (window.confirm("Sei sicuro di voler svuotare il giro visite del giorno?")) {
      saveTourList([]);
    }
  };

  // Helper to get category styles
  const getCategoryClass = (cat) => {
    switch (cat) {
      case 'Trasporti e Logistica': return 'badge-trasporti';
      case 'Automotive e Officine': return 'badge-automotive';
      case 'Edilizia e Costruzioni': return 'badge-edilizia';
      case 'Servizi e Cooperative': return 'badge-servizi';
      case 'Agricoltura e Floricoltura': return 'badge-agricoltura';
      case 'Alimentari e Ristorazione': return 'badge-alimentari';
      default: return 'badge-altro';
    }
  };

  const getCategoryColor = (cat) => {
    switch (cat) {
      case 'Trasporti e Logistica': return '#f97316';
      case 'Automotive e Officine': return '#3b82f6';
      case 'Edilizia e Costruzioni': return '#a855f7';
      case 'Servizi e Cooperative': return '#06b6d4';
      case 'Agricoltura e Floricoltura': return '#10b981';
      case 'Alimentari e Ristorazione': return '#f43f5e';
      default: return '#64748b';
    }
  };

  // Export tour to CSV
  const exportTourCSV = () => {
    if (tourList.length === 0) return;
    
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Nome,Indirizzo,Comune,Provincia,Categoria,Latitudine,Longitudine\n";
    
    tourList.forEach(c => {
      const row = [
        `"${c.name.replace(/"/g, '""')}"`,
        `"${(c.address || '').replace(/"/g, '""')}"`,
        `"${c.city || ''}"`,
        `"${c.province || ''}"`,
        `"${c.category || ''}"`,
        c.lat || '',
        c.lng || ''
      ].join(",");
      csvContent += row + "\n";
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Giro_Visite_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="dashboard-container">
      {/* SIDEBAR FOR FILTERS AND PLANNING */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>
            <MapPin size={24} className="text-accent" />
            Visite Planner
          </h1>
          <p>Gestione clientela sul territorio sardo</p>
        </div>
        
        <div className="sidebar-content">
          {/* SEARCH AND FILTERS */}
          <div className="filter-section">
            <h2 className="filter-title">Ricerca e Filtri</h2>
            
            <div className="search-input-wrapper">
              <Search size={18} />
              <input
                type="text"
                placeholder="Cerca cliente o indirizzo..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
              />
            </div>
            
            <div className="select-wrapper">
              <label className="select-label">Filtra per Provincia</label>
              <select 
                value={selectedProvince} 
                onChange={handleProvinceChange}
                className="select-control"
              >
                <option value="">Tutte le province</option>
                {provincesList.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            
            <div className="select-wrapper">
              <label className="select-label">Filtra per Comune</label>
              <select
                value={selectedComune}
                onChange={(e) => setSelectedComune(e.target.value)}
                className="select-control"
                disabled={comuniList.length === 0}
              >
                <option value="">Tutti i comuni</option>
                {comuniList.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>
          
          {/* CATEGORY PILLS */}
          <div className="filter-section">
            <h2 className="filter-title">Filtra per Tipologia</h2>
            <div className="category-pills">
              {categoriesList.map(cat => {
                const isActive = selectedCategories.includes(cat);
                return (
                  <button
                    key={cat}
                    onClick={() => toggleCategory(cat)}
                    className={`category-pill ${isActive ? 'active' : ''}`}
                  >
                    <span 
                      className="category-dot" 
                      style={{ backgroundColor: getCategoryColor(cat) }} 
                    />
                    {cat}
                  </button>
                );
              })}
            </div>
          </div>
          
          {/* TOUR VISITS PLANNER */}
          <div className="planner-section">
            <div className="planner-header">
              <h2 className="filter-title">Giro Visite del Giorno</h2>
              <span className="badge">{tourList.length}</span>
            </div>
            
            {tourList.length === 0 ? (
              <p className="empty-tour-text">
                Nessun cliente aggiunto al giro visite. Clicca sui punti in mappa o sulla tabella per aggiungerne.
              </p>
            ) : (
              <div className="tour-list">
                {tourList.map(item => (
                  <div key={item.id} className="tour-item">
                    <div className="tour-item-info">
                      <div className="tour-item-name">{item.name}</div>
                      <div className="tour-item-sub">
                        {item.city} ({item.province})
                      </div>
                    </div>
                    <button 
                      onClick={() => removeFromTour(item.id)} 
                      className="btn-remove"
                      title="Rimuovi"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            
            {tourList.length > 0 && (
              <div className="action-buttons">
                <button onClick={exportTourCSV} className="btn btn-secondary">
                  <FileText size={16} />
                  Esporta CSV
                </button>
                <button onClick={() => window.print()} className="btn btn-primary">
                  <Printer size={16} />
                  Stampa Giro
                </button>
              </div>
            )}
            
            {tourList.length > 0 && (
              <button onClick={clearTour} className="btn btn-secondary" style={{borderColor: 'rgba(239, 68, 68, 0.2)', color: 'var(--accent-danger)'}}>
                <Trash2 size={16} />
                Svuota Giro
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="main-content">
        {/* STATS OVERVIEW */}
        <div className="stats-row">
          <div className="stat-card">
            <div className="stat-icon">
              <Briefcase size={20} />
            </div>
            <div className="stat-info">
              <div className="stat-val">{clients.length}</div>
              <div className="stat-lbl">Totale Clienti</div>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon warning">
              <Layers size={20} />
            </div>
            <div className="stat-info">
              <div className="stat-val">{filteredClients.length}</div>
              <div className="stat-lbl">Filtro Attivo</div>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon success">
              <CheckSquare size={20} />
            </div>
            <div className="stat-info">
              <div className="stat-val">{tourList.length}</div>
              <div className="stat-lbl">Visite Pianificate</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon" style={{color: '#a855f7', background: 'rgba(168, 85, 247, 0.1)'}}>
              <Award size={20} />
            </div>
            <div className="stat-info">
              <div className="stat-val">
                {clients.length > 0 ? Math.round((filteredClients.length / clients.length) * 100) : 0}%
              </div>
              <div className="stat-lbl">Copertura Target</div>
            </div>
          </div>
        </div>

        {/* INTERACTIVE MAP CONTAINER */}
        <div className="map-card">
          <div className="map-header-bar">
            <div className="map-title">
              <Map size={16} />
              Mappa di Pianificazione Territoriale
            </div>
            <div className="map-legend">
              <div className="legend-item"><span className="category-dot dot-trasporti"/>Flotte</div>
              <div className="legend-item"><span className="category-dot dot-automotive"/>Officine</div>
              <div className="legend-item"><span className="category-dot dot-edilizia"/>Edilizia</div>
              <div className="legend-item"><span className="category-dot dot-agricoltura"/>Agricolo</div>
              <div className="legend-item"><span className="category-dot dot-altro"/>Altro</div>
            </div>
          </div>
          
          <div className="map-container">
            <MapContainer 
              center={mapCenter} 
              zoom={mapZoom} 
              style={{ width: '100%', height: '100%' }}
              zoomControl={true}
            >
              <MapUpdater center={mapCenter} zoom={mapZoom} />
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              />
              
              {/* Plot clients with coordinates */}
              {filteredClients
                .filter(c => c.lat && c.lng)
                .map(client => {
                  const isInTour = tourList.some(item => item.id === client.id);
                  return (
                    <CircleMarker
                      key={client.id}
                      center={[client.lat, client.lng]}
                      radius={isInTour ? 9 : 6}
                      fillColor={getCategoryColor(client.category)}
                      color={isInTour ? "#ffffff" : getCategoryColor(client.category)}
                      weight={isInTour ? 2 : 1}
                      opacity={1}
                      fillOpacity={isInTour ? 0.95 : 0.7}
                    >
                      <Popup className="custom-popup">
                        <div className="popup-container">
                          <div className="popup-name">{client.name}</div>
                          <div className={`popup-category ${getCategoryClass(client.category)}`}>
                            {client.category}
                          </div>
                          <div className="popup-address">{client.address}</div>
                          <button
                            onClick={() => isInTour ? removeFromTour(client.id) : addToTour(client)}
                            className="btn-popup-add"
                            style={{
                              backgroundColor: isInTour ? 'var(--accent-danger)' : 'var(--accent-primary)'
                            }}
                          >
                            {isInTour ? "Rimuovi dal Giro" : "Aggiungi al Giro"}
                          </button>
                        </div>
                      </Popup>
                    </CircleMarker>
                  );
                })
              }
            </MapContainer>
          </div>
        </div>

        {/* DATA TABLE VIEW */}
        <div className="table-card">
          <div className="table-header-bar">
            <div className="table-title">
              <FileText size={16} />
              Elenco Clienti Filtrati ({filteredClients.length})
            </div>
            <div style={{fontSize: '11px', color: 'var(--text-muted)'}}>
              *Solo le attività con coordinate geolocalizzate appaiono sulla mappa.
            </div>
          </div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>Comune</th>
                  <th>Prov.</th>
                  <th>Categoria</th>
                  <th>Stato Mappa</th>
                  <th>Azioni</th>
                </tr>
              </thead>
              <tbody>
                {filteredClients.slice(0, 100).map(client => {
                  const isInTour = tourList.some(item => item.id === client.id);
                  const hasCoords = client.lat && client.lng;
                  return (
                    <tr key={client.id}>
                      <td style={{fontWeight: '600'}}>{client.name}</td>
                      <td>{client.city}</td>
                      <td>{client.province}</td>
                      <td>
                        <span className={`cell-category ${getCategoryClass(client.category)}`}>
                          {client.category}
                        </span>
                      </td>
                      <td>
                        {hasCoords ? (
                          <span style={{color: 'var(--accent-success)'}}>Geolocalizzato</span>
                        ) : (
                          <span style={{color: 'var(--text-muted)', fontStyle: 'italic'}}>Nessuna coord.</span>
                        )}
                      </td>
                      <td>
                        <button
                          onClick={() => isInTour ? removeFromTour(client.id) : addToTour(client)}
                          className="btn-table-add"
                          style={{
                            color: isInTour ? 'var(--accent-danger)' : 'var(--accent-primary)'
                          }}
                        >
                          {isInTour ? "Rimuovi" : "Aggiungi"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {filteredClients.length > 100 && (
                  <tr>
                    <td colSpan="6" style={{textAlign: 'center', color: 'var(--text-muted)', padding: '15px'}}>
                      Mostrati i primi 100 risultati di {filteredClients.length}. Usa i filtri nella barra laterale per affinare la ricerca.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* PRINT-ONLY TEMPLATE */}
      <div className="print-page">
        <div className="print-header">
          <h1>GIRO VISITE DEL GIORNO</h1>
          <p>Data: {new Date().toLocaleDateString('it-IT')} | Tappe Programmate: {tourList.length}</p>
        </div>
        <table className="print-table">
          <thead>
            <tr>
              <th style={{width: '5%'}}>#</th>
              <th style={{width: '30%'}}>Cliente</th>
              <th style={{width: '45%'}}>Indirizzo</th>
              <th style={{width: '20%'}}>Settore / Note</th>
            </tr>
          </thead>
          <tbody>
            {tourList.map((item, index) => (
              <tr key={item.id}>
                <td>{index + 1}</td>
                <td style={{fontWeight: 'bold'}}>{item.name}</td>
                <td>{item.address}</td>
                <td>{item.category}</td>
              </tr>
            ))}
          </tbody>
        </table>
        
        <div className="print-notes">
          <h3>NOTE DI VIAGGIO:</h3>
          <div className="print-notes-box"></div>
        </div>
      </div>
    </div>
  );
}

export default App;
