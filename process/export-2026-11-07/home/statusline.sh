#!/bin/bash

input=$(cat)

# persist rate-limit windows so watchers can read the reset time
{ echo "$input" | jq -c '{rate_limits, ts: now}' > ~/.claude/cache/rate_limits.json.tmp \
    && mv ~/.claude/cache/rate_limits.json.tmp ~/.claude/cache/rate_limits.json; } 2>/dev/null

# --- context ---
ctx_pct=$(echo "$input" | jq -r '.context_window.used_percentage // 1 | round')

# --- tokens ---
in_last=$(echo "$input" | jq '.context_window.current_usage.input_tokens // 0')
out_last=$(echo "$input" | jq '.context_window.current_usage.output_tokens // 0')

in_total=$(echo "$input" | jq '.context_window.total_input_tokens // 0')
out_total=$(echo "$input" | jq '.context_window.total_output_tokens // 0')
total=$((in_total + out_total))

# --- rate limits ---
pct_5h=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // 1 | round')
pct_wk=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // 1 | round')

reset_5h=$(echo "$input" | jq '.rate_limits.five_hour.resets_at // 0')
reset_wk=$(echo "$input" | jq '.rate_limits.seven_day.resets_at // 0')

now=$(date +%s)

# --- time remaining formatter ---
fmt_time() {
  local diff=$1
  if (( diff <= 0 )); then
    echo "0m"
    return
  fi

  local h=$((diff / 3600))
  local m=$(((diff % 3600) / 60))

  if (( h > 0 )); then
    printf "%dh%02dm" "$h" "$m"
  else
    printf "%dm" "$m"
  fi
}

rem_5h=$(fmt_time $((reset_5h - now)))
rem_wk=$(fmt_time $((reset_wk - now)))

# --- gradient function (green → yellow → red) ---
color_pct() {
  local pct=$1
  if (( pct < 50 )); then
    echo "\033[32m"   # green
  elif (( pct < 75 )); then
    echo "\033[33m"   # yellow
  else
    echo "\033[31m"   # red
  fi
}

# --- colors ---
RESET="\033[0m"
BOLD="\033[1m"

ctx_color=$(color_pct "$ctx_pct")
h5_color=$(color_pct "$pct_5h")
wk_color=$(color_pct "$pct_wk")

TOK_COLOR="\033[36m"  # cyan (stable, not gradient)

# --- reset trigger ---
show_reset=0
if (( ctx_pct >= 70 )) || (( in_last >= 6000 )); then
  show_reset=1
fi

# --- output ---
printf "%bCTX:%3s%%%b | %bTOK:%b ↑%s ↓%s Σ%s | %b5H:%s%%(%s)%b %bWK:%s%%(%s)%b%b\n" \
  "$ctx_color$BOLD" "$ctx_pct" "$RESET" \
  "$TOK_COLOR$BOLD" "$RESET" "$in_last" "$out_last" "$total" \
  "$h5_color$BOLD" "$pct_5h" "$rem_5h" "$RESET" \
  "$wk_color$BOLD" "$pct_wk" "$rem_wk" "$RESET" \
  "$( ((show_reset)) && printf '\033[31m ↻\033[0m' )"
