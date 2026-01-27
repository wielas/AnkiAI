# Flashcards - rag_k3

**Configuration:** RAG with top_k=3 (three most relevant chunks)

**Generated:** 2026-01-27T09:28:05.442746

---

## Card 1 (Page 205)

**Question:**
Why is it impractical to configure all followers as synchronous in leader-based replication, and what approach is commonly used instead?

**Answer:**
If all followers were synchronous, any single node outage would block all writes and halt the entire system since the leader must wait for all followers to confirm. Instead, databases typically use semi-synchronous replication where only one follower is synchronous while others are asynchronous, guaranteeing an up-to-date copy on at least two nodes (leader and one synchronous follower) without risking complete system unavailability.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.6140291464833916, 0.557036100102916, 0.50744703799564]
- Context tokens: 2076

---

## Card 2 (Page 206)

**Question:**
In leader-based replication, why is it impractical to configure all followers as synchronous replicas?

**Answer:**
If all followers were synchronous, any single node outage would halt the entire system because the leader must wait for confirmation from all followers before processing writes. In practice, databases use semi-synchronous replication with only one synchronous follower, ensuring data durability on at least two nodes while maintaining system availability.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.5620517663883368, 0.528148567976193, 0.5070067693311181]
- Context tokens: 2076

---

## Card 3 (Page 207)

**Question:**
Why is it impractical to configure all followers as synchronous in leader-based replication, and what configuration is commonly used instead?

**Answer:**
If all followers were synchronous, any single node failure would block all writes and halt the entire system. In practice, databases use semi-synchronous replication where only one follower is synchronous while others are asynchronous, guaranteeing an up-to-date copy exists on at least two nodes (the leader and one synchronous follower) without sacrificing availability.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.6262702835310096, 0.5761893544643316, 0.5691123562651079]
- Context tokens: 2076

---

## Card 4 (Page 208)

**Question:**
Why is it impractical for all followers to be synchronous in leader-based replication, and what is the typical compromise solution?

**Answer:**
If all followers were synchronous, any single node outage would block all writes and halt the entire system. The typical compromise is semi-synchronous replication, where one follower is synchronous and others are asynchronous, guaranteeing an up-to-date copy on at least two nodes (the leader and one synchronous follower) while maintaining system availability.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.6600500942340486, 0.6103992546217675, 0.5316499900085185]
- Context tokens: 2076

---

## Card 5 (Page 209)

**Question:**
Why is it impractical for all followers to be synchronous in leader-based replication, and what is the common solution?

**Answer:**
If all followers were synchronous, any single node outage would block all writes and halt the entire system. The common solution is semi-synchronous replication: one follower is synchronous while others are asynchronous, guaranteeing an up-to-date copy on at least two nodes (the leader and one synchronous follower). If the synchronous follower becomes unavailable, an asynchronous one is promoted to synchronous.

**RAG Metadata:**
- Chunks retrieved: 3
- Top scores: [0.6351286708616848, 0.5634294434354615, 0.508732548457387]
- Context tokens: 2076

---

