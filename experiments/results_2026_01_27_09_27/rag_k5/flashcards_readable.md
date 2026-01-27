# Flashcards - rag_k5

**Configuration:** RAG with top_k=5 (default, five most relevant chunks)

**Generated:** 2026-01-27T09:28:26.389797

---

## Card 1 (Page 205)

**Question:**
Why is it impractical to configure all followers as synchronous in leader-based replication, and what compromise is typically used instead?

**Answer:**
If all followers were synchronous, any single node outage would halt the entire system since the leader must wait for all followers to confirm writes. The typical compromise is semi-synchronous replication, where one follower is synchronous (guaranteeing an up-to-date copy on at least two nodes) and the others are asynchronous, with another follower promoted to synchronous if the current one becomes unavailable.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.6140809058105646, 0.557217703053784, 0.507496771506642]
- Context tokens: 2076

---

## Card 2 (Page 206)

**Question:**
Why is it impractical to configure all followers as synchronous in leader-based replication, and what is the common compromise?

**Answer:**
If all followers were synchronous, any single node outage would block all writes and halt the entire system. The common compromise is semi-synchronous replication, where one follower is synchronous and others are asynchronous, guaranteeing an up-to-date copy on at least two nodes (leader and one synchronous follower) while maintaining system availability.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.5620051490626021, 0.5281191745367803, 0.5069760051772109]
- Context tokens: 2076

---

## Card 3 (Page 207)

**Question:**
Why is it impractical for all followers to use synchronous replication in leader-based database systems?

**Answer:**
If all followers were synchronous, any single node outage would block all writes and halt the entire system, since the leader must wait for confirmation from every follower before processing writes. In practice, systems use semi-synchronous replication (one synchronous follower, others asynchronous) to balance data durability with system availability.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.6263938596046799, 0.5761841699515702, 0.569058480325778]
- Context tokens: 2076

---

## Card 4 (Page 208)

**Question:**
Why is it impractical for all followers to be synchronous in leader-based replication, and what is the typical compromise solution?

**Answer:**
If all followers were synchronous, any single node outage would block all writes and halt the entire system. The typical compromise is semi-synchronous replication, where one follower is synchronous (guaranteeing up-to-date data on at least two nodes) and the others are asynchronous. If the synchronous follower becomes unavailable, one asynchronous follower is promoted to synchronous.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.6601064490078563, 0.61058432498783, 0.5316418023201428]
- Context tokens: 2076

---

## Card 5 (Page 209)

**Question:**
Why is it impractical to configure all followers as synchronous in leader-based replication, and what is the common alternative approach?

**Answer:**
If all followers were synchronous, any single node failure would block all writes and halt the entire system since the leader must wait for confirmation from every follower. The practical solution is semi-synchronous replication: one follower is synchronous (guaranteeing an up-to-date copy on at least two nodes), while others are asynchronous. If the synchronous follower fails, an asynchronous one is promoted to synchronous.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.6351518980450657, 0.56326326569975, 0.5087131738793627]
- Context tokens: 2076

---

