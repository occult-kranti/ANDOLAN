foreach (name in ["func_bomb_target", "info_player_terrorist", "info_player_counterterrorist"]) {
    local instance = null;
    local count = 0;
    while ((instance = Entities.FindByClassname(instance, name)) != null) {
        count += 1;
    }
    printl("YUGA_ENTITY " + name + " " + count);
}
