# Flashcards - baseline

**Configuration:** Baseline: Full page text without RAG

**Generated:** 2026-01-27T09:04:23.105769

---

## Card 1 (Page 222)

**Question:**
How does monotonic reads guarantee differ from eventual consistency, and what anomaly does it prevent?

**Answer:**
Monotonic reads is stronger than eventual consistency by guaranteeing that if a user makes sequential reads, they will not see time go backward (i.e., not read older data after reading newer data). It prevents the anomaly where a user reads from a fresh replica first, then from a stale replica, making it appear as if their previous read never happened.

---

## Card 2 (Page 223)

**Question:**
What problem does the consistent prefix reads guarantee solve in distributed systems with replication lag?

**Answer:**
It prevents causality violations where an observer might see events out of order, such as seeing a reply before the original question. This occurs when different partitions have varying replication lag, causing causally dependent writes to appear in the wrong sequence.

---

## Card 3 (Page 224)

**Question:**
Why does consistent prefix anomaly particularly occur in partitioned databases, and what is the fundamental cause?

**Answer:**
In partitioned databases, different partitions operate independently without a global ordering of writes. This means users may read some parts of the database in an older state and others in a newer state, violating the guarantee that causally related writes appear in the same order to all readers.

---

## Card 4 (Page 225)

**Question:**
What is the primary architectural difference between single-leader and multi-leader replication, and what problem does multi-leader replication solve?

**Answer:**
Multi-leader replication allows multiple nodes to accept writes simultaneously (rather than routing all writes through a single leader), with each leader forwarding changes to other leaders. This solves the availability problem where clients cannot write to the database if they lose connection to the single leader due to network interruptions.

---

## Card 5 (Page 226)

**Question:**
How does multi-leader replication improve write performance compared to single-leader replication in a multi-datacenter deployment?

**Answer:**
In multi-leader replication, writes can be processed in the local datacenter and replicated asynchronously to other datacenters, hiding inter-datacenter network delay from users. In contrast, single-leader replication requires all writes to go over the internet to the datacenter containing the leader, adding significant latency.

---

## Card 6 (Page 227)

**Question:**
Why does a multi-leader replication configuration tolerate network problems between datacenters better than a single-leader configuration?

**Answer:**
Multi-leader configurations use asynchronous replication, allowing each datacenter to process writes independently without waiting for confirmation across the inter-datacenter link. In contrast, single-leader configurations perform writes synchronously over the inter-datacenter link, making them highly sensitive to network interruptions that would block all write operations.

---

## Card 7 (Page 228)

**Question:**
Why is offline calendar syncing across multiple devices considered an example of multi-leader replication?

**Answer:**
Each device acts as a leader with its own local database that accepts write requests independently. Changes are asynchronously replicated between all devices when internet connectivity is available, with replication lag potentially lasting hours or days depending on network availability.

---

