# TODO - Dashboard UX/UI Glassmorphism + Datos Chart.js

- [ ] Entender y revisar estructura actual del dashboard (index.html) y endpoint /api/dashboard/
- [ ] Planificar la arquitectura de estilos: archivo CSS dedicado (frontend/static/css/dashboard.css) + vínculo en dashboard/index.html o base.html
- [ ] Implementar Glassmorphism: fondo clínico, tarjetas translúcidas con blur, bordes redondeados, sombras suaves
- [ ] Implementar animaciones: fade-in al cargar + hover con elevación/gradiente + transiciones suaves
- [ ] Ajustar HTML: añadir clases/IDs para animaciones (p.ej. .glass-card, .reveal)
- [ ] Verificar conexión de datos reales: asegurar que índices/propiedades JS (kpi_resumen y grafica_*) coincidan con backend
- [x] Actualizar dashboard/index.html para renderizar KPIs y gráficas con animaciones
- [ ] Revisar/ajustar el “is-visible” (IntersectionObserver) en scroll y aplicar clases reveal a todas las tarjetas si aplica

- [ ] Probar visualmente en navegador y validar que Chart.js recibe datos (sin vacío)

