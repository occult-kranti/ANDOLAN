// SPDX-License-Identifier: GPL-3.0-only
// Research fixture for OpenMW's pinned components/misc/objectpool.hpp.
// Original harness written for the YUGA source study. Not game runtime code.
#include <iostream>
#include <utility>
#include "components/misc/objectpool.hpp"

struct Item {
    static inline int constructed = 0;
    static inline int destroyed = 0;
    int payload = 0;
    Item() { ++constructed; }
    ~Item() { ++destroyed; }
};
int checks = 0;
int failures = 0;
void check(const char* name, bool ok) {
    ++checks;
    if (!ok) ++failures;
    std::cout << "{\"case\":\"" << name << "\",\"passed\":" << (ok ? "true" : "false") << "}\n";
}
int main() {
    Misc::ObjectPtr<Item> empty;
    empty.reset(); empty.reset();
    check("default_null_and_duplicate_null_reset_are_safe", !empty);
    {
        Misc::ObjectPool<Item> pool;
        auto first = pool.get();
        auto second = pool.get();
        check("two_live_borrows_are_distinct", first.get() != second.get() && Item::constructed == 2);
        Item* recycled = first.get();
        first->payload = 73;
        first.reset(); first.reset();
        auto next = pool.get();
        check("duplicate_reset_does_not_duplicate_free_entry", next.get() == recycled && next.get() != second.get());
        check("recycle_avoids_new_construction", Item::constructed == 2);
        check("pool_does_not_reset_payload_for_the_caller", next->payload == 73);
        Misc::ObjectPtr<Item> moved = std::move(next);
        check("unique_borrow_move_transfers_ownership", !next && moved.get() == recycled);
        second.reset(); moved.reset();
        {
            auto a = pool.get(); auto b = pool.get(); auto c = pool.get();
            check("pool_has_no_hard_capacity_guard", Item::constructed == 3 && a && b && c);
        }
        for (int i = 0; i < 10000; ++i) { auto one = pool.get(); one->payload = i; }
        check("fixed_concurrency_reuse_has_no_further_item_growth", Item::constructed == 3);
    }
    check("pool_destruction_releases_retained_items", Item::destroyed == Item::constructed && Item::destroyed == 3);
    std::cout << "{\"passed\":" << (failures ? "false" : "true") << ",\"checks\":" << checks << ",\"failures\":" << failures << "}\n";
    return failures ? 1 : 0;
}
