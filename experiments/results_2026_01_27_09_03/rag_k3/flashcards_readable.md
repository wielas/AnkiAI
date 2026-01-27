# Flashcards - rag_k3

**Configuration:** RAG with top_k=3 (three most relevant chunks)

**Generated:** 2026-01-27T09:05:20.917627

---

## Card 1 (Page 222)

**Question:**
How does monotonic reads guarantee differ from eventual consistency, and what is one implementation approach to achieve it?

**Answer:**
Monotonic reads ensures that if a user makes sequential reads, they will not see time go backward (i.e., won't read older data after reading newer data), which is stronger than eventual consistency but weaker than strong consistency. It can be implemented by routing each user's reads to the same replica consistently, such as by hashing the user ID to select their replica.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.6307883305097299, 0.488226606398215, 0.4557946547225391]
- Context tokens: 1888

---

## Card 2 (Page 223)

**Question:**
How does monotonic reads guarantee differ from eventual consistency, and what is a common implementation approach to achieve it?

**Answer:**
Monotonic reads ensures that if a user makes several reads in sequence, they will not see time go backward (i.e., won't read older data after reading newer data), which is stronger than eventual consistency but weaker than strong consistency. It's commonly implemented by routing each user's reads to the same replica (e.g., based on a hash of the user ID) rather than randomly selecting replicas.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.5006224503704744, 0.429988642110429, 0.39426034637500407]
- Context tokens: 1888

---

## Card 3 (Page 224)

**Question:**
What is consistent prefix reads and why is it particularly problematic in partitioned databases?

**Answer:**
Consistent prefix reads guarantees that if a sequence of writes happens in a certain order, anyone reading those writes will see them appear in the same order, preserving causality. This is problematic in partitioned databases because different partitions operate independently without a global ordering of writes, causing observers to potentially see some parts of the database in an older state and others in a newer state, violating causal relationships.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.5227036851303698, 0.5045983667368419, 0.4565322758748452]
- Context tokens: 1888

---

## Card 4 (Page 225)

**Question:**
Why does consistent prefix reads become a particular problem in partitioned databases, and how can causally related writes help prevent this anomaly?

**Answer:**
In partitioned databases, different partitions operate independently without a global ordering of writes, causing readers to see some parts in older states and others in newer states (e.g., seeing an answer before the question). Writing causally related data to the same partition ensures these writes maintain their order, preventing the anomaly where effects appear before their causes.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.5477727644371053, 0.4820826853254621, 0.472952228070488]
- Context tokens: 2174

---

## Card 5 (Page 226)

**Question:**
Why does multi-leader replication typically provide better write performance than single-leader replication in a multi-datacenter deployment?

**Answer:**
In multi-leader replication, writes can be processed in the local datacenter and replicated asynchronously to other datacenters, hiding the inter-datacenter network delay from users. In contrast, single-leader replication requires every write to go over the internet to the datacenter with the leader, adding significant latency.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.6477178903501122, 0.6062469407092561, 0.5753094044233821]
- Context tokens: 2174

---

## Card 6 (Page 227)

**Question:**
Why does multi-leader replication provide better performance than single-leader replication in a multi-datacenter deployment?

**Answer:**
In multi-leader replication, writes can be processed in the local datacenter and replicated asynchronously to other datacenters, hiding inter-datacenter network delay from users. In contrast, single-leader replication requires every write to go over the internet to the datacenter with the leader, adding significant latency.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.621546717449804, 0.5719502594794157, 0.5304979258294588]
- Context tokens: 2174

---

## Card 7 (Page 228)

**Question:**
Why is multi-leader replication particularly well-suited for offline-capable applications like calendar apps, and what architectural consideration does this create?

**Answer:**
Each device acts as an independent leader with its own local database that accepts writes while offline, then asynchronously syncs changes when reconnected. This creates extremely high replication lag (hours or days) and makes the system architecturally similar to multi-datacenter replication, where each device is essentially a "datacenter" connected by highly unreliable networks.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.52239393020755, 0.4394716705387455, 0.438858352044148]
- Context tokens: 2174

---

