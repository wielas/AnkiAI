# Flashcards - rag_k5

**Configuration:** RAG with top_k=5 (default, five most relevant chunks)

**Generated:** 2026-01-27T09:05:49.642359

---

## Card 1 (Page 222)

**Question:**
How does monotonic reads guarantee differ from eventual consistency, and what is a common implementation strategy to achieve it?

**Answer:**
Monotonic reads guarantees that if a user makes several reads in sequence, they will not see time go backward (i.e., not read older data after reading newer data), which is stronger than eventual consistency but weaker than strong consistency. It is commonly implemented by ensuring each user always reads from the same replica, often by routing based on a hash of the user ID.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.6309525376511388, 0.48840256079524896, 0.4558378004518488]
- Context tokens: 2664

---

## Card 2 (Page 223)

**Question:**
How does the consistent prefix reads guarantee prevent causality violations in distributed databases with replication lag?

**Answer:**
Consistent prefix reads ensures that if a sequence of writes happens in a certain order, anyone reading those writes will see them appear in the same order. This prevents scenarios where causally dependent data (like a question and its answer) appear out of sequence due to different replication speeds across partitions, which would violate causality.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.500465020489956, 0.43009790324524005, 0.39425689981816053]
- Context tokens: 2664

---

## Card 3 (Page 224)

**Question:**
What problem does the consistent prefix reads guarantee solve in distributed databases with partitioned data?

**Answer:**
Consistent prefix reads ensures that if a sequence of writes happens in a certain order, readers will see them in the same order, preventing causality violations. This is particularly important in partitioned databases where different partitions may replicate at different speeds, which could otherwise cause observers to see effects before their causes (e.g., seeing an answer before the question that prompted it).

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.5229261369250294, 0.5045482437183545, 0.4565515818817455]
- Context tokens: 2664

---

## Card 4 (Page 225)

**Question:**
Why does the consistent prefix reads anomaly particularly occur in partitioned databases, and how does it violate causality?

**Answer:**
In partitioned databases, different partitions operate independently without a global ordering of writes. This means a reader may see some partitions in a newer state and others in an older state, causing causally related writes (like a question and its answer) to appear out of order. This violates causality because an effect can appear to occur before its cause.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.5480000655880053, 0.482104877797168, 0.47292295150636016]
- Context tokens: 2664

---

## Card 5 (Page 226)

**Question:**
How does multi-leader replication in a multi-datacenter setup improve performance compared to single-leader replication?

**Answer:**
In multi-leader replication, each write can be processed in the local datacenter and replicated asynchronously to other datacenters, hiding the inter-datacenter network delay from users. In contrast, single-leader replication requires every write to go over the internet to the datacenter with the leader, adding significant latency.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.6477238419378047, 0.6060563018586077, 0.575277249581286]
- Context tokens: 2664

---

## Card 6 (Page 227)

**Question:**
Why does multi-leader replication improve write performance in a multi-datacenter deployment compared to single-leader replication?

**Answer:**
In multi-leader replication, writes can be processed in the local datacenter and replicated asynchronously to other datacenters, hiding inter-datacenter network delay from users. In contrast, single-leader replication requires every write to go over the internet to the datacenter with the leader, adding significant latency.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.6215129394312561, 0.5718703471368862, 0.5305050886030431]
- Context tokens: 2664

---

## Card 7 (Page 228)

**Question:**
Why is multi-leader replication particularly well-suited for offline-capable applications like calendar apps, and what architectural perspective does this represent?

**Answer:**
Each device acts as a local leader accepting writes independently, with asynchronous replication syncing changes when connectivity is restored. This is architecturally equivalent to multi-datacenter multi-leader replication taken to the extreme, where each device is a "datacenter" connected by extremely unreliable networks, with replication lag potentially spanning hours or days.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.522356277514849, 0.43945016761598066, 0.4389065259644518]
- Context tokens: 2664

---

