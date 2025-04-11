# data/sample_data.py
# Datos de muestra para el desarrollo y pruebas

# Partidos de Progol
progol_matches = {
    "main": [
        {"id": 1, "home": "América", "away": "Cruz Azul", "date": "2023-04-14"},
        {"id": 2, "home": "Guadalajara", "away": "Monterrey", "date": "2023-04-14"},
        {"id": 3, "home": "Tigres", "away": "Puebla", "date": "2023-04-15"},
        {"id": 4, "home": "Santos", "away": "Pachuca", "date": "2023-04-15"},
        {"id": 5, "home": "Atlas", "away": "León", "date": "2023-04-16"},
        {"id": 6, "home": "Necaxa", "away": "Mazatlán", "date": "2023-04-16"},
        {"id": 7, "home": "Juárez", "away": "Toluca", "date": "2023-04-16"},
        {"id": 8, "home": "Pumas", "away": "San Luis", "date": "2023-04-17"},
        {"id": 9, "home": "Querétaro", "away": "Atlético San Luis", "date": "2023-04-17"},
        {"id": 10, "home": "Monarcas", "away": "Dorados", "date": "2023-04-18"},
        {"id": 11, "home": "Tijuana", "away": "Veracruz", "date": "2023-04-18"},
        {"id": 12, "home": "Celaya", "away": "Venados", "date": "2023-04-19"},
        {"id": 13, "home": "Zacatecas", "away": "Oaxaca", "date": "2023-04-19"},
        {"id": 14, "home": "Cancún", "away": "Tapachula", "date": "2023-04-20"}
    ],
    "revenge": [
        {"id": 15, "home": "América", "away": "Monterrey", "date": "2023-04-21"},
        {"id": 16, "home": "Guadalajara", "away": "Cruz Azul", "date": "2023-04-21"},
        {"id": 17, "home": "Tigres", "away": "Pachuca", "date": "2023-04-22"},
        {"id": 18, "home": "Santos", "away": "Puebla", "date": "2023-04-22"},
        {"id": 19, "home": "Atlas", "away": "León", "date": "2023-04-23"},
        {"id": 20, "home": "Necaxa", "away": "Mazatlán", "date": "2023-04-23"},
        {"id": 21, "home": "Juárez", "away": "Toluca", "date": "2023-04-24"}
    ]
}

# Partidos en vivo de muestra
live_matches_sample = [
    {
        "id": 1001,
        "home": "América",
        "away": "Cruz Azul",
        "homeScore": 2,
        "awayScore": 1,
        "minute": 78,
        "status": "live",
        "homeLogo": "https://via.placeholder.com/30",
        "awayLogo": "https://via.placeholder.com/30",
        "result": "L"
    },
    {
        "id": 1002,
        "home": "Guadalajara",
        "away": "Monterrey",
        "homeScore": 0,
        "awayScore": 0,
        "minute": 45,
        "status": "live",
        "homeLogo": "https://via.placeholder.com/30",
        "awayLogo": "https://via.placeholder.com/30",
        "result": "E"
    }
]

# Próximos partidos de muestra
upcoming_matches_sample = [
    {
        "id": 1003,
        "home": "Tigres",
        "away": "Puebla",
        "date": "2023-04-15T17:00:00",
        "homeLogo": "https://via.placeholder.com/30",
        "awayLogo": "https://via.placeholder.com/30",
        "status": "NS"
    },
    {
        "id": 1004,
        "home": "Santos",
        "away": "Pachuca",
        "date": "2023-04-15T19:00:00",
        "homeLogo": "https://via.placeholder.com/30",
        "awayLogo": "https://via.placeholder.com/30",
        "status": "NS"
    },
    {
        "id": 1005,
        "home": "Atlas",
        "away": "León",
        "date": "2023-04-16T12:00:00",
        "homeLogo": "https://via.placeholder.com/30",
        "awayLogo": "https://via.placeholder.com/30",
        "status": "NS"
    }
]