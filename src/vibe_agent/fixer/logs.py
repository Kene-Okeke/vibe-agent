TAIL_LINES = 80 
ERROR_WORDS = ["error", "err!", "failed", "cannot find", "not found"]

def trim_log(log: str) ->str:
    lines = log.splitlines()

     # short log: nothing to trim
    if len(lines) <= TAIL_LINES:
        return log

    # the last 80 lines: where builds usually fail
    last_lines = lines[-TAIL_LINES:]

    # everything BEFORE the last 80 lines
    earlier = lines[:-TAIL_LINES]

    # keep earlier lines that mention an error
    error_lines = []
    for line in earlier:
        lowered = line.lower()
        for word in ERROR_WORDS:
            if word in lowered:
                error_lines.append(line)
                break

    # glue: the error lines (max 20), a marker, then the last 80 lines
    kept = error_lines[-20:] + ["... (log trimmed) ..."] + last_lines
    return "\n".join(kept)