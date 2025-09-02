# Stock Scanner Makefile

.PHONY: help build test deploy clean backup restore logs status

# Default environment
ENV ?= production

help: ## Show this help message
	@echo "Stock Scanner Deployment Commands"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	@echo "🔨 Building Docker images..."
	docker-compose -f docker-compose.prod.yml build

test: ## Run tests
	@echo "🧪 Running tests..."
	cd backend && python -m pytest tests/ -v
	cd frontend && npm test -- --watchAll=false

deploy: ## Deploy to specified environment (ENV=production|staging)
	@echo "🚀 Deploying to $(ENV) environment..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
		powershell -ExecutionPolicy Bypass -File scripts/deploy.ps1 -Environment $(ENV); \
	else \
		bash scripts/deploy.sh $(ENV); \
	fi

clean: ## Clean up Docker resources
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose -f docker-compose.prod.yml down -v
	docker system prune -f

backup: ## Create backup
	@echo "🗄️ Creating backup..."
	bash scripts/backup.sh

restore: ## Restore from backup (BACKUP_DATE required)
	@echo "🔄 Restoring from backup..."
	@if [ -z "$(BACKUP_DATE)" ]; then \
		echo "❌ BACKUP_DATE is required. Usage: make restore BACKUP_DATE=20240101_120000"; \
		exit 1; \
	fi
	bash scripts/restore.sh $(BACKUP_DATE)

logs: ## Show service logs
	@echo "📝 Showing service logs..."
	docker-compose -f docker-compose.prod.yml logs -f

status: ## Show service status
	@echo "📊 Service status:"
	docker-compose -f docker-compose.prod.yml ps
	@echo ""
	@echo "🏥 Health checks:"
	@curl -s http://localhost:8000/health | jq . || echo "Backend not responding"
	@curl -s http://localhost/health || echo "Frontend not responding"

dev: ## Start development environment
	@echo "🔧 Starting development environment..."
	docker-compose up -d postgres
	cd backend && python run_server.py &
	cd frontend && npm start

stop: ## Stop all services
	@echo "🛑 Stopping all services..."
	docker-compose -f docker-compose.prod.yml down

restart: ## Restart all services
	@echo "🔄 Restarting all services..."
	docker-compose -f docker-compose.prod.yml restart

update: ## Update and redeploy
	@echo "🔄 Updating and redeploying..."
	git pull
	$(MAKE) build
	$(MAKE) deploy ENV=$(ENV)

ssl-setup: ## Set up SSL certificates (requires manual certificate files)
	@echo "🔒 Setting up SSL certificates..."
	@mkdir -p nginx/ssl
	@echo "Please place your SSL certificate files in nginx/ssl/:"
	@echo "  - cert.pem (certificate file)"
	@echo "  - key.pem (private key file)"

monitoring: ## Show monitoring dashboard
	@echo "📊 Monitoring information:"
	@echo "Metrics: http://localhost:8000/metrics"
	@echo "Health: http://localhost:8000/health"
	@curl -s http://localhost:8000/metrics | jq . || echo "Metrics not available"