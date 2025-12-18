# 📚 Migration History

> **Historical documentation of major refactoring efforts**

This directory contains documentation from major architecture refactoring projects.

---

## 📑 Available Migration Docs

### [Index Refactor](index-refactor.md)

**Original:** `MIGRATION_INDEX.md`

**Summary:** Complete refactoring of the indexing/search layer to clean architecture.

**Key changes:**
- Moved from monolithic index to protocol-based design
- Separated vector search, keyword search, and hybrid strategies
- Introduced `VectorStore` Protocol for database abstraction
- Created `IndexService` for high-level operations

**Timeline:** Earlier refactoring phase

---

### [Ingestion Refactor](ingestion-refactor.md)

**Original:** `MIGRATION_INGESTION.md`

**Summary:** Refactoring of document ingestion pipeline.

**Key changes:**
- Protocol-based parsers (`DocumentParser`, `OCREngine`)
- Separated parsing from indexing
- Language detection integration
- Chunking strategy abstraction

**Timeline:** Earlier refactoring phase

---

### [Index Summary](index-summary.md)

**Original:** `REFACTOR_INDEX_SUMMARY.md`

**Summary:** High-level summary of index refactoring decisions and outcomes.

**Highlights:**
- Why we chose Protocol-based design
- Performance improvements achieved
- Migration path for existing code
- Lessons learned

---

### [Ingestion Summary](ingestion-summary.md)

**Original:** `REFACTOR_SUMMARY.md`

**Summary:** High-level summary of ingestion refactoring decisions and outcomes.

**Highlights:**
- Parser abstraction benefits
- OCR integration approach
- Chunking strategy evolution
- Testing strategy

---

## 🎯 Purpose of Migration Docs

These documents serve as:

1. **Historical Record** - Understanding past decisions
2. **Learning Resource** - See refactoring patterns in practice
3. **Context** - Why current architecture looks this way
4. **Reference** - Handling future refactorings

---

## 🔄 Current Architecture

For up-to-date architecture documentation, see:

- [Architecture Overview](../architecture/overview.md)
- [Architecture Decisions (ADRs)](../architecture/decisions.md)
- [Core Layer](../core/README.md)
- [Infra Layer](../infra/README.md)

---

## 📝 Notes

- These docs are kept for historical reference
- May contain outdated code examples
- Focus on understanding refactoring patterns, not copying code
- Current implementation may have evolved further

---

**[⬆️ Documentation Home](../README.md)**

*Last updated: 2025-12-18*
