import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css'; // Twoje style przycisków
// Pamiętaj, że index.css musi być zaimportowany w main.jsx lub tutaj!

const Dashboard = () => {
  const navigate = useNavigate();

  const sections = [
    {
      title: "Moduł Słowników",
      items: [
        { name: "Podmioty", path: "/podmioty", type: "react" },
        { name: "Obszary", path: "http://localhost:8000/obszary/", type: "django" },
        { name: "Bloki", path: "http://localhost:8000/bloki/", type: "django" },
        { name: "Podbloki", path: "http://localhost:8000/podblok/", type: "django" },
        { name: "Pytania", path: "http://localhost:8000/pytania/", type: "django" },
        { name: "Podzapytania", path: "http://localhost:8000/podzapytania/", type: "django" },
        { name: "Grupy", path: "http://localhost:8000/grupy-naglowkow/", type: "django" },
        { name: "Ankiety", path: "http://localhost:8000/ankieta-naglowek/", type: "django" },
      ]
    },
    {
      title: "Moduł Formularzy",
      items: [
        { name: "Powiązanie podmiotu z grupą", path: "http://localhost:8000/grupy-podmiotow/", type: "django" },
        { name: "Powiązanie ankiety z pytaniami", path: "http://localhost:8000/ankieta-pytania/", type: "django" },
      ]
    },
    {
      title: "Generowanie ankiet",
      items: [
        { name: "Generuj", path: "http://localhost:8000/generowanie-formularzy/", type: "django" },
      ]
    }
  ];

  return (
    <div className="app-container">
      {/* TO MUSI MIEĆ TĘ KLASĘ */}
      <header className="app-header-main">
        <h1 className="header-centered-title">
          Generator arkuszy oceny jakościowej podmiotów finansowych
        </h1>
      </header>

      <main className="app-main">
        <div className="flex gap-6 h-full max-w-[1600px] mx-auto items-stretch">
          {sections.map((section, idx) => (
            <div key={idx} className="db-column">
              <div className="db-column-header">
                <h2 className="db-column-title">{section.title}</h2>
                <div className="db-column-line"></div>
              </div>
              <div className="db-btn-wrapper">
                <div className={`grid-standard ${idx === 0 ? 'grid-slowniki' : 'grid-pozostale'}`}>
                  {section.items.map((item, i) => (
                    <button
                      key={i}
                      onClick={() => navigate(item.path)}
                      className="db-green-btn"
                    >
                      {item.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </main>

      <footer className="app-footer-main">
        © 2025 URZĄD KOMISJI NADZORU FINANSOWEGO
      </footer>
    </div>
  );
};

export default Dashboard;