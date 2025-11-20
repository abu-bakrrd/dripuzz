# Universal E-Commerce Telegram Mini App Template

## Overview

This project provides a universal, configurable template for creating e-commerce Telegram Mini Apps. Its primary purpose is to enable users to set up an online shop by modifying JSON configuration files, eliminating the need for code changes. Key capabilities include a mobile-first, minimal design, customizable pastel color palettes, and touch-optimized interactions. The template aims to simplify the creation and deployment of e-commerce solutions within the Telegram ecosystem, offering a robust and flexible platform for various businesses.

## User Preferences

I prefer iterative development with clear, concise explanations at each step. I like clean, functional code and expect the agent to ask before making any significant architectural or design changes. Do not make changes to files within the `docs/` folder.

## System Architecture

### Frontend

The frontend is built with React 18 and TypeScript, utilizing Vite for building and development. Data fetching and state management are handled by TanStack Query (React Query). UI components leverage Shadcn/ui, built on Radix UI primitives, styled with Tailwind CSS for dynamic theming. Core features include a `useConfig` hook for global configuration access, `ThemeApplier` for dynamic color scheme injection, `FontLoader` for custom font management, and a `formatPrice` utility for currency display.

### Backend

The backend is a Flask 3.1.2 application, written in Python. It uses `psycopg2-binary` for PostgreSQL database interactions and serves the pre-built React frontend.

**API Endpoints:**
- `GET /api/config`: Retrieves shop configuration.
- `GET /config/<filename>`: Serves static files from the config directory.
- `GET /api/categories`: Lists all product categories.
- `GET /api/products`: Lists products, with optional category filtering.
- `GET /api/products/<id>`: Retrieves a single product by ID.
- `POST /api/auth/telegram`: Handles Telegram user authentication.
- Additional endpoints support cart and favorites functionality.

### Database

The system uses PostgreSQL. The database schema includes tables for `users`, `categories`, `products`, `favorites`, and `cart`. Categories and product details, including product colors (TEXT[] array) and up to two universal attributes (JSONB: name + values), are stored in the database, while UI/branding configurations reside in JSON files. The system supports automatic database initialization and optional remote PostgreSQL access with secure configuration.

### Configuration

All shop settings are centralized in `config/settings.json`, covering:
- `shopName`, `description`, `logo`
- `currency`: `symbol`, `code`, `position`
- `managerContact`: Telegram handle
- `colorScheme`: Customizable pastel palette (e.g., `background`, `foreground`, `primary`)
- `sortOptions`: Dynamic sort options with emojis
- `ui`: `maxWidth`, `productsPerPage`, `showCategoryIcons`, `showPriceFilter`
- `texts`: Customizable UI labels
- `fonts`: `fontFamily`, `fontFile`, `productName` (weight), `price` (weight), `description` (weight)
- `logoSize`: Configurable logo display size

### Deployment

Deployment supports fully automated (`auto_deploy.sh`) and interactive (`deploy_vps.sh`) methods for VPS environments. It handles environment variable setup, GitHub integration for cloning, automatic database initialization, Nginx configuration, and Telegram bot deployment as a systemd service. Remote database access can be enabled via `enable_remote_db.sh`.

## External Dependencies

-   **Database:** Neon Serverless PostgreSQL
-   **UI Components:** Radix UI, Shadcn/ui, Lucide React (for iconography)
-   **Fonts:** Google Fonts (Inter, Poppins)