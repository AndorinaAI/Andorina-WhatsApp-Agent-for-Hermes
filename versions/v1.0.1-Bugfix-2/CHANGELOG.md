# 📝 Changelog - Andoriña v1.0.1 (Bugfix-2)

## [v1.0.1-Bugfix-2] - 2026-05-09
**"The Pure Code Update" / "La Actualización de Código Puro"**

---

### 🇺🇸 English

#### 🛠️ Web Refactoring & Stability
- **Eliminated Inline Styles:** Complete migration of 30+ `style="..."` attributes to semantic classes in `styles.css`. This ensures compatibility with strict linters and improves performance.
- **Structural Validation:** Fixed tag nesting and normalized tag endings to achieve 100% W3C HTML5 compliance.
- **Legal Sync:** Fixed footer internal links that were pointing to non-existent sections in translations. Terms of Use, Privacy, and License policies are now perfectly linked.
- **Character Sanitization:** Normalized UTF-8 encoding and replaced problematic characters to prevent rendering errors in legacy editors.

#### 🛡️ Security & Accessibility
- **Safe Navigation:** Implemented `rel="noopener noreferrer"` on all external links to prevent "tabnabbing" security risks.
- **SVG Namespaces:** Added `xmlns` to all vector icons for flawless XML/HTML validation.
- **ARIA Enhancements:** Added accessibility attributes (`aria-label`) so screen readers correctly identify dynamic features.

#### 📦 Repository Management
- **Professional History:** Cleaned and consolidated commits (Squash) to present a professional and clear timeline on GitHub.
- **Version Parity:** Ensured absolute parity between the main website and the files contained in the version package.

---

### 🇪🇸 Español

#### 🛠️ Refactorización y Estabilidad Web
- **Adiós a los Estilos Inline:** Migración total de más de 30 estilos `style="..."` a clases semánticas en `styles.css`. Esto garantiza compatibilidad con linters estrictos y mejora la velocidad de carga.
- **Validación Estructural:** Corrección de anidamiento de etiquetas y normalización de cierres de etiquetas para cumplir con el estándar HTML5 de la W3C al 100%.
- **Sincronización Legal:** Corregidos enlaces internos en el pie de página que apuntaban a secciones inexistentes en las traducciones. Ahora los términos de uso, privacidad y licencias están perfectamente vinculados.
- **Limpieza de Caracteres:** Normalización de codificación UTF-8 y sustitución de caracteres problemáticos para evitar errores de renderizado en editores antiguos.

#### 🛡️ Seguridad y Accesibilidad
- **Navegación Segura:** Implementación de `rel="noopener noreferrer"` en todos los enlaces externos para prevenir ataques de "tabnabbing".
- **Espacios de Nombres SVG:** Añadido `xmlns` a todos los iconos vectoriales para una validación XML/HTML impecable.
- **Mejora ARIA:** Añadidos atributos de accesibilidad (`aria-label`) para que lectores de pantalla identifiquen correctamente las funciones dinámicas.

#### 📦 Gestión de Repositorio
- **Historial Profesional:** Limpieza y consolidación de commits (Squash) para presentar una línea de tiempo clara y profesional en GitHub.
- **Sincronización de Versiones:** Asegurada la paridad absoluta entre la web principal y los archivos contenidos en el paquete de versión.

---
*Developed with &#10084; by Jorge.*
