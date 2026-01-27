# Flashcards - baseline

**Configuration:** Baseline: Full page text without RAG

**Generated:** 2026-01-27T09:27:24.516677

---

## Card 1 (Page 205)

**Question:**
Why does replication become difficult when the replicated data changes over time, and what is the primary focus of replication algorithms?

**Answer:**
Static data only needs to be copied once to each node, but changing data requires mechanisms to propagate updates consistently across all replicas. Replication algorithms (single-leader, multi-leader, and leaderless) focus on handling these changes while managing trade-offs like synchronous vs. asynchronous propagation and failure handling.

---

## Card 2 (Page 206)

**Question:**
In leader-based replication, how do followers ensure they maintain the same data as the leader?

**Answer:**
Followers receive a replication log or change stream from the leader containing all data changes. They apply these writes to their local storage in the same order as they were processed on the leader, ensuring data consistency across replicas.

---

## Card 3 (Page 207)

**Question:**
Why are followers considered read-only from the client's perspective in leader-based replication?

**Answer:**
Followers are read-only because they only receive and apply data changes forwarded from the leader, rather than accepting write operations directly from clients. This ensures all writes go through a single point (the leader) to maintain consistency across replicas.

---

## Card 4 (Page 208)

**Question:**
Why is it impractical to configure all followers as synchronous in leader-based replication?

**Answer:**
If all followers were synchronous, any single node outage would block all writes and halt the entire system, since the leader must wait for confirmation from all synchronous followers before processing writes. In practice, only one follower is typically synchronous while others remain asynchronous to balance consistency with availability.

---

## Card 5 (Page 209)

**Question:**
What is the main trade-off when using fully asynchronous replication in leader-based systems?

**Answer:**
Fully asynchronous replication sacrifices durability (writes may be lost if the leader fails before replication) in exchange for availability and performance, allowing the leader to continue processing writes even when all followers are slow or unavailable.

---

