# Flashcards - rag_k10

**Configuration:** RAG with top_k=10 (ten most relevant chunks)

**Generated:** 2026-01-27T09:06:16.096158

---

## Card 1 (Page 222)

**Question:**
How does monotonic reads guarantee differ from eventual consistency, and what is one implementation approach to achieve it?

**Answer:**
Monotonic reads ensures that if a user makes sequential reads, they won't see time go backward (i.e., won't read older data after reading newer data), which is stronger than eventual consistency but weaker than strong consistency. It can be implemented by routing each user's reads to the same replica (e.g., based on a hash of the user ID), ensuring they see a consistent progression of data states.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.6306623508370425, 0.48832130470368124, 0.45568675186254165]
- Context tokens: 2664

---

## Card 2 (Page 223)

**Question:**
How does the monotonic reads guarantee prevent anomalies in eventually consistent systems, and what is a common implementation approach?

**Answer:**
Monotonic reads ensures that if a user makes several reads in sequence, they will not see time go backward (i.e., not read older data after having previously read newer data). This is commonly implemented by routing each user's reads to the same replica (e.g., based on a hash of the user ID), so they don't alternate between fresh and stale replicas.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.5006224503704744, 0.4300877155384125, 0.39425689981816053]
- Context tokens: 2664

---

## Card 3 (Page 224)

**Question:**
What problem does the consistent prefix reads guarantee solve in distributed databases, and why does it particularly occur in partitioned systems?

**Answer:**
Consistent prefix reads ensures that if writes happen in a certain order, readers will see them in the same order, preventing causality violations (like seeing an answer before the question). This problem occurs in partitioned databases because different partitions operate independently without a global ordering of writes, allowing users to see some partitions in older states and others in newer states simultaneously.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.5231043782621111, 0.5046010529926244, 0.4565515818817455]
- Context tokens: 2664

---

## Card 4 (Page 225)

**Question:**
Why is multi-leader replication particularly well-suited for multi-datacenter deployments compared to single-leader replication?

**Answer:**
Multi-leader replication allows each datacenter to process writes locally with a leader in each datacenter, hiding inter-datacenter network delay from users and improving perceived performance. It also provides better tolerance for datacenter outages and network problems since each datacenter can operate independently, with asynchronous replication catching up when connectivity is restored.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.5480478972734242, 0.482104877797168, 0.47292295150636016]
- Context tokens: 2664

---

## Card 5 (Page 226)

**Question:**
In a multi-datacenter deployment, how does multi-leader replication improve write performance compared to single-leader replication?

**Answer:**
Multi-leader replication processes writes in the local datacenter and replicates asynchronously to other datacenters, hiding inter-datacenter network delay from users. In contrast, single-leader replication requires every write to go over the internet to the datacenter with the leader, adding significant latency.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.64768623374281, 0.6059515180015163, 0.5752418045127425]
- Context tokens: 2664

---

## Card 6 (Page 227)

**Question:**
How does multi-leader replication improve write performance in a multi-datacenter deployment compared to single-leader replication?

**Answer:**
In multi-leader replication, each datacenter has its own leader that processes writes locally and replicates asynchronously to other datacenters, hiding inter-datacenter network delay from users. In contrast, single-leader replication requires all writes to go over the internet to the single datacenter with the leader, adding significant latency.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.6215129394312561, 0.5717966152066563, 0.5305050886030431]
- Context tokens: 2664

---

## Card 7 (Page 228)

**Question:**
Why is multi-leader replication particularly well-suited for applications with offline operation, such as calendar apps across multiple devices?

**Answer:**
Each device acts as a local leader that accepts writes independently when offline, then asynchronously syncs changes with other devices when connectivity is restored. This architecture allows users to continue reading and writing data regardless of internet availability, with the replication lag potentially spanning hours or days until devices reconnect.

**RAG Metadata:**
- Chunks retrieved: 4
- Top scores: [0.5223395591824708, 0.4394465072637789, 0.43893612900940376]
- Context tokens: 2664

---

