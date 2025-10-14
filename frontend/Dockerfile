# ==============================================================================
# STAGE 1: DEPENDENCIES - Instalacja node_modules
# ==============================================================================
FROM node:20-alpine AS deps

WORKDIR /app

# Kopiuj tylko package files NAJPIERW (dla lepszego layer caching)
# Jeśli package.json/package-lock.json się nie zmienią, ta warstwa zostanie użyta z cache
COPY package*.json ./

# Zainstaluj dependencies
# --prefer-offline: Użyj lokalnego cache jeśli możliwe
# --frozen-lockfile: Nie modyfikuj package-lock.json (dla consistency)
RUN npm ci --prefer-offline --no-audit

# ==============================================================================
# STAGE 2: BUILDER - Build produkcyjny (tylko dla production target)
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Kopiuj node_modules z deps stage
COPY --from=deps /app/node_modules ./node_modules

# Kopiuj kod źródłowy
COPY . .

# Build produkcyjny aplikacji
# Tworzy zoptymalizowane static files w /app/dist
RUN npm run build

# ==============================================================================
# STAGE 3A: DEVELOPMENT - Vite dev server z hot reload
# ==============================================================================
FROM node:20-alpine AS development

WORKDIR /app

# Kopiuj node_modules z deps stage (NIE instalujemy ponownie!)
COPY --from=deps /app/node_modules ./node_modules

# Kopiuj kod źródłowy
# W docker-compose montujemy volume, więc to będzie nadpisane
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Uruchom dev server
# --host 0.0.0.0: Pozwala na dostęp z hosta (nie tylko localhost)
# --port 5173: Wymuszony port
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# ==============================================================================
# STAGE 3B: PRODUCTION - Nginx serwujący static build
# ==============================================================================
FROM nginx:alpine AS production

# Kopiuj zbudowane static files z builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Kopiuj custom nginx config (dla React Router - SPA routing)
# Jeśli plik nie istnieje, użyj default nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf 2>/dev/null || echo "Using default nginx config"

# Expose nginx port
EXPOSE 80

# Nginx startuje automatycznie w foreground (daemon off)
CMD ["nginx", "-g", "daemon off;"]

# ==============================================================================
# DLACZEGO MULTI-STAGE BUILD DLA FRONTEND?
# ==============================================================================
# 1. DEVELOPMENT:
#    - node_modules kopiowane z cache (NIE npm install przy każdym starcie!)
#    - Vite dev server z hot reload
#    - Volume mount dla live code changes
#
# 2. PRODUCTION:
#    - Statyczne pliki serwowane przez nginx (SZYBKO!)
#    - Brak Node.js w runtime (bezpieczeństwo + rozmiar)
#    - Image size: ~25MB (nginx + static files) vs ~500MB (node + dependencies)
#
# 3. CACHING:
#    - Dependencies layer cached dopóki package.json się nie zmieni
#    - Kod aplikacji może się zmieniać bez reinstalacji dependencies
#    - Build time: ~5-10s (cached) vs ~60-90s (full install)
# ==============================================================================

# Default target to development (można nadpisać w docker-compose)
FROM development
