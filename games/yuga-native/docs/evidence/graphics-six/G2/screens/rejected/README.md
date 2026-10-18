# Initial parse finding

The first run could not infer a Boolean from the dynamically typed runtime player reload field. It produced a script parse error and was explicitly terminated (exit 143); no passing assertion receipt was produced. The HUD local now declares `waiting: bool`. The separate accepted reruns compile cleanly and retain all assertions. This diagnostic is excluded from the 202 passing checks.
