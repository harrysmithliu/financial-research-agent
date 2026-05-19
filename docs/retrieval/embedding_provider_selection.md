# Embedding Provider Selection

## Purpose
Define the current embedding provider strategy for retrieval baseline work, including cost-first defaults, swap conditions, and configuration constraints.

## Intended Audience
- RAG / Retrieval Agent
- Ingestion / Backend Agent
- MCP Gateway / Tooling Agent
- Maintainers who operate local runtime

## Scope
This document covers provider selection for embedding generation only. It does not define generation-model policy.

## Current Decision (Batch 0 Draft)
- Provider path: OpenAI-compatible adapter first
- Default tier: low-cost embedding model
- Dimension policy: prefer low dimension for baseline where supported; otherwise use model-native dimension
- Replacement policy: revisit after retrieval baseline metrics are stable

## Decision Inputs To Confirm In Later Batches
- Exact model ID and fallback model ID
- Final dimension value and compatibility constraints
- Rate-limit, retry, and cache policy defaults
- Cost guardrails per ingestion run

## Change Control
Any change to provider/model/dimension must update this file and the latest retrieval handoff entry.

---
Created By: RAG / Retrieval Agent (Codex)
Created At (UTC): 2026-05-19T18:40:15Z
