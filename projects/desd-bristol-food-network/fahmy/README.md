# Bristol Regional Food Network Marketplace

A Django-based digital marketplace prototype that connects local food producers with customers around Bristol. The project supports product discovery, producer inventory management, multi-vendor ordering, mock payments, order tracking, finance reporting, and community content such as recipes and farm stories.

This was built as a full-stack academic/team project and is structured to show practical backend, database, Docker, and user-flow implementation.

## Key Features

- Customer product discovery with search, filters, categories, seasonal availability, organic status, allergens, food miles, and price sorting.
- Producer product management for creating, editing, hiding, and tracking stock levels.
- Cart and checkout flow for single-producer and multi-producer orders.
- Mock payment service with automatic 5% platform commission and producer payout calculations.
- Producer order dashboard with suborders, delivery details, and status updates.
- Finance dashboards for admin reporting, settlements, payout records, and CSV/PDF-style exports.
- Customer order history, reorder support, receipts, and recurring weekly orders.
- Community engagement through verified reviews, producer replies, recipes, storage guidance, and farm stories.

## Tech Stack

- Python
- Django
- PostgreSQL
- Docker Compose
- FastAPI mock payments service
- HTML/CSS templates

## Project Structure

- `src/accounts` - login, registration, logout, and role-based redirects.
- `src/market_products` - product discovery, producer product management, recipes, reviews, and farm stories.
- `src/market_orders` - producer order dashboards and suborder status handling.
- `src/market_payments` - cart, checkout, receipts, payment records, and order history.
- `src/market_finance` - admin finance dashboards, settlements, exports, and recurring orders.
- `payments` - mock FastAPI payment/commission service.

## Running Locally

Create an environment file:

```bash
cp .env.example .env
```

Build and start the Docker stack:

```bash
docker compose up --build
```

Apply database migrations:

```bash
docker compose run --rm web python src/manage.py migrate
```

Optional demo data:

```bash
docker compose run --rm web python src/manage.py seed_full_demo
docker compose run --rm web python src/manage.py seed_engagement_demo
```

Open the app:

```text
http://localhost:8000
```

## Testing

Run the Django test suite:

```bash
docker compose run --rm web python src/manage.py test
```

Run system checks:

```bash
docker compose run --rm web python src/manage.py check
```

## Service URLs

- Web app: `http://localhost:8000`
- Mock payments API health check: `http://localhost:8001/api/payments/health`

## Notes

The payment system is a mock/test implementation for development and demonstration only. It does not use real payment details or live financial processing.
