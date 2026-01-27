# Flashcards - rag_k1

**Configuration:** RAG with top_k=1 (single most relevant chunk)

**Generated:** 2026-01-27T09:04:52.750777

---

## Card 1 (Page 222)

**Question:**
How does monotonic reads guarantee differ from eventual consistency, and what is a common implementation approach?

**Answer:**
Monotonic reads ensures that if a user makes sequential reads, they will not see older data after having read newer data (time doesn't go backward), which is stronger than eventual consistency but weaker than strong consistency. This is commonly implemented by routing each user's reads to the same replica, often chosen by hashing the user ID.

**RAG Metadata:**
- Chunks retrieved: 1
- Top scores: [0.6307208884910953]
- Context tokens: 488

---

## Card 2 (Page 223)

**Question:**
How does monotonic reads guarantee differ from eventual consistency, and what implementation approach can achieve it?

**Answer:**
Monotonic reads ensures that if a user makes sequential reads, they won't see older data after having read newer data (time doesn't go backward), which is stronger than eventual consistency but weaker than strong consistency. It can be implemented by routing each user's reads to the same replica, such as by hashing the user ID to select a consistent replica.

**RAG Metadata:**
- Chunks retrieved: 1
- Top scores: [0.500465020489956]
- Context tokens: 488

---

## Card 3 (Page 224)

**Question:**
What is a consistent prefix read anomaly and why does it commonly occur in partitioned databases?

**Answer:**
A consistent prefix read anomaly occurs when a reader observes writes out of their original order, such as seeing an answer before the question that prompted it. This happens in partitioned databases because different partitions operate independently without a global write ordering, causing readers to see some partitions in older states and others in newer states.

**RAG Metadata:**
- Chunks retrieved: 1
- Top scores: [0.5229240343632439]
- Context tokens: 882

---

## Card 4 (Page 225)

**Question:**
What is a consistent prefix read anomaly and why does it occur in partitioned databases?

**Answer:**
A consistent prefix read anomaly occurs when a reader observes events out of their original order, such as seeing an answer before the question that prompted it. This happens in partitioned databases because different partitions operate independently without a global ordering of writes, causing readers to see some partitions in older states and others in newer states.

**RAG Metadata:**
- Chunks retrieved: 1
- Top scores: [0.5480242489033531]
- Context tokens: 882

---

## Card 5 (Page 226)

**Question:**
How does multi-leader replication improve write performance in a multi-datacenter deployment compared to single-leader replication?

**Answer:**
In multi-leader replication, writes can be processed in the local datacenter and replicated asynchronously to other datacenters, hiding inter-datacenter network delay from users. In contrast, single-leader replication requires every write to go over the internet to the datacenter with the leader, adding significant latency.

**RAG Metadata:**
- Chunks retrieved: 1
- Top scores: [0.64768623374281]
- Context tokens: 774

---

## Card 6 (Page 227)

**Question:**
In a multi-datacenter deployment, how does multi-leader replication improve write performance compared to single-leader replication?

**Answer:**
Multi-leader replication allows writes to be processed in the local datacenter and replicated asynchronously to other datacenters, hiding inter-datacenter network delay from users. In contrast, single-leader replication requires every write to go over the internet to the datacenter with the leader, adding significant latency.

**RAG Metadata:**
- Chunks retrieved: 1
- Top scores: [0.6215129394312561]
- Context tokens: 774

---

## Card 7 (Page 228)

**Question:**
Why is multi-leader replication particularly suitable for offline-capable applications like calendar apps?

**Answer:**
Each device acts as a local leader that accepts writes independently while offline, then asynchronously syncs changes when connectivity is restored. This architecture allows continuous read and write operations regardless of internet availability, with replication lag potentially spanning hours or days until the next sync opportunity.

**RAG Metadata:**
- Chunks retrieved: 1
- Top scores: [0.5223395591824708]
- Context tokens: 514

---

