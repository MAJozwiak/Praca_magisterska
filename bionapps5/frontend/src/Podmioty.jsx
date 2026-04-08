import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const Podmioty = () => {
  const navigate = useNavigate();
  const [podmioty, setPodmioty] = useState([]);
  const [filters, setFilters] = useState({ kod: '', nazwa: '' });
  const [form, setForm] = useState({ kod: '', nazwa: '' });

  const fetchPodmioty = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:8000/api/podmioty/');
      setPodmioty(res.data);
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchPodmioty(); }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.kod || !form.nazwa) return;
    try {
      await axios.post('http://127.0.0.1:8000/api/podmioty/', form);
      setForm({ kod: '', nazwa: '' });
      fetchPodmioty();
    } catch (err) { alert("Błąd zapisu."); }
  };

  const filtered = podmioty.filter(p =>
    p.kod.toLowerCase().includes(filters.kod.toLowerCase()) &&
    p.nazwa.toLowerCase().includes(filters.nazwa.toLowerCase())
  );

  return (
    <div className="app-container">
      <header className="app-header-main">
        <h1 className="header-centered-title">Ewidencja Podmiotów Nadzorowanych</h1>
        <button onClick={() => navigate('/')} className="btn-header-back">POWRÓT</button>
      </header>

      {/* gap-2 zamiast gap-4 daje więcej miejsca dla tabeli */}
      <main className="flex-1 overflow-hidden p-3 flex flex-col gap-2">
        <div className="flex flex-col h-full w-full max-w-[1600px] mx-auto gap-2">

          {/* SEKCJA 1: DODAWANIE */}
          <section className="modern-card">
            <div className="card-accent-bar"></div>
            <div className="card-content">
              <h3 className="card-title">DODAJ NOWY PODMIOT</h3>
              <form onSubmit={handleAdd} className="flex items-end gap-4">
                <div className="w-[150px]">
                  <label className="input-label">KOD</label>
                  <input className="input-field" type="text" value={form.kod} onChange={e => setForm({...form, kod: e.target.value})} placeholder="000"/>
                </div>
                <div className="w-[500px]">
                  <label className="input-label">PEŁNA NAZWA INSTYTUCJI</label>
                  <input className="input-field" type="text" value={form.nazwa} onChange={e => setForm({...form, nazwa: e.target.value})} placeholder="Wpisz nazwę..."/>
                </div>
                <button type="submit" className="btn-navy w-[160px] !h-[34px]">DODAJ REKORD</button>
              </form>
            </div>
          </section>

          {/* SEKCJA 2: FILTROWANIE */}
          <section className="modern-card">
            <div className="card-accent-bar"></div>
            <div className="card-content">
              <div className="flex justify-between items-center mb-1">
                <h3 className="card-title !mb-0">FILTRUJ LISTĘ</h3>
                <div className="bg-[#003366] text-white text-[9px] font-black px-3 py-0.5 rounded uppercase">
                  WYNIKÓW: {filtered.length}
                </div>
              </div>
              <div className="flex items-end gap-4">
                <div className="w-[150px]">
                  <label className="input-label">SZUKAJ KODU</label>
                  <input className="input-field" type="text" value={filters.kod} onChange={e => setFilters({...filters, kod: e.target.value})} placeholder="Filtruj..."/>
                </div>
                <div className="w-[500px]">
                  <label className="input-label">SZUKAJ NAZWY</label>
                  <input className="input-field" type="text" value={filters.nazwa} onChange={e => setFilters({...filters, nazwa: e.target.value})} placeholder="Szukaj..."/>
                </div>
                <div className="w-[160px]"></div>
              </div>
            </div>
          </section>

          {/* TABELA - TERAZ POWINNA BYĆ WYRAŹNIE WIĘKSZA */}
          <div className="table-container">
            <div className="overflow-y-auto custom-scrollbar h-full">
              <table className="modern-table">
                <thead>
                  <tr>
                    <th className="w-[4%]">KOD IDENTYFIKACYJNY</th>
                    <th className="w-[60%]" >PEŁNA NAZWA INSTYTUCJI</th>
                    <th className="text-right w-[20%]">OPCJE</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(p => (
                    <tr key={p.id}>
                      <td className="font-bold text-[#003366] w-[150px]">{p.kod}</td>
                      <td className="uppercase font-bold text-slate-800 tracking-tight">{p.nazwa}</td>
                      <td className="text-right">
                        <span className="btn-delete">USUŃ REKORD</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>

      <footer className="app-footer-main">© 2025 URZĄD KOMISJI NADZORU FINANSOWEGO</footer>
    </div>
  );
};

export default Podmioty;