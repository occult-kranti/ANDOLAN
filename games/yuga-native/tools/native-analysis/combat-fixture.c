/* Original YUGA toolchain fixture. No reference-game code or assets. */
#include <stdio.h>

__attribute__((noinline)) int clamp_armour(int armour) {
    if (armour < 0) return 0;
    if (armour > 100) return 100;
    return armour;
}

__attribute__((noinline)) int combat_damage(int power, int armour, int shield) {
    if (power <= 0) return 0;
    int damage = power - clamp_armour(armour) / 2;
    if (shield) damage /= 2;
    return damage < 1 ? 1 : damage;
}

int main(void) {
    struct { int power, armour, shield, expected; } cases[] = {
        {100, 40, 0, 80}, {100, 40, 1, 40}, {0, 50, 0, 0},
        {20, 200, 0, 1}, {20, -5, 0, 20}
    };
    for (unsigned i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        int actual = combat_damage(cases[i].power, cases[i].armour, cases[i].shield);
        if (actual != cases[i].expected) return 1;
    }
    puts("original-fixture: 5 cases passed");
    return 0;
}
