# Flashcards - rag_k1

**Configuration:** RAG with top_k=1 (single most relevant chunk)

**Generated:** 2026-01-27T09:27:44.892655

---

## Card 1 (Page 205)

**Question:**
Why does replication become complex when data changes over time, and what are the three main algorithmic approaches to handle this complexity?

**Answer:**
Replication is easy for static data but becomes complex when handling changes to replicated data across multiple nodes. The three popular algorithms for replicating changes are single-leader, multi-leader, and leaderless replication, each with different trade-offs in consistency, availability, and performance.

**RAG Metadata:**
- Chunks retrieved: 1
- Top scores: [0.614088750256355]
- Context tokens: 405

---

## Card 2 (Page 206)

**Question:**
In leader-based replication, why are follower replicas typically read-only from the client's perspective?

**Answer:**
Followers are read-only to ensure all writes are processed through the leader first, which then propagates changes to followers via the replication log. This maintains data consistency by ensuring all writes are applied in the same order across all replicas.

**RAG Metadata:**
- Chunks retrieved: 1
- Top scores: [0.5620517663883368]
- Context tokens: 836

---

## Card 3 (Page 207)

**Question:**
In leader-based replication, why are write operations only accepted by the leader node rather than by any replica?

**Answer:**
The leader processes all writes first to establish a single, authoritative ordering of operations. It then propagates these changes to followers via a replication log, ensuring all replicas apply writes in the same order and maintain data consistency across the system.

**RAG Metadata:**
- Chunks retrieved: 1
- Top scores: [0.6262702835310096]
- Context tokens: 836

---

## Card 4 (Page 208)

**Question:**
Why is it impractical to configure all followers as synchronous in leader-based replication, and what is the common solution?

**Answer:**
If all followers were synchronous, any single node outage would halt the entire system since the leader must wait for all followers to confirm writes. The common solution is semi-synchronous replication: one follower is synchronous while others are asynchronous, guaranteeing an up-to-date copy on at least two nodes (the leader and one synchronous follower).

**RAG Metadata:**
- Chunks retrieved: 1
- Top scores: [0.6599284578633808]
- Context tokens: 831

---

## Card 5 (Page 209)

**Question:**
Why is it impractical to configure all followers as synchronous in leader-based replication, and what is the typical compromise solution?

**Answer:**
If all followers were synchronous, any single node outage would halt the entire system since the leader must wait for all followers to confirm writes. The typical compromise is semi-synchronous replication, where one follower is synchronous and others are asynchronous, guaranteeing an up-to-date copy on at least two nodes (the leader and one synchronous follower) while maintaining system availability.

**RAG Metadata:**
- Chunks retrieved: 1
- Top scores: [0.635116817477681]
- Context tokens: 831

---

