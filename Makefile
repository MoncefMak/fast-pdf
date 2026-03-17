.PHONY: dev release test bench check clean

# Développement : compile + installe dans le venv
# NE JAMAIS faire de cp manuel — maturin gère tout
dev:
	maturin develop

# Release : compile optimisé
release:
	maturin develop --release

# Tests
test: dev
	cargo test --workspace
	pytest tests/ -v

# Benchmarks vs WeasyPrint
bench: release
	python bench/compare.py

# Check Rust seulement
check:
	cargo check --workspace
	cargo clippy --workspace -- -D warnings

# Nettoyer
clean:
	cargo clean
	find . -name "*.so" -delete
	find . -name "__pycache__" -exec rm -rf {} +
