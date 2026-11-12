# WO-47 draft SDC for the C9 digital macro (tt_um_sd_adc_c9), clk = 48 MHz (SPEC 3.8a).
# DRAFT: input/output budgets below are first estimates; the C4 / C3 numbers come from their PEX runs.
# No false paths, no multicycle paths, no case analysis: every endpoint is timed (pd-expert rule 4).

set clk_period 20.833
create_clock -name clk -period $clk_period [get_ports clk]
set_clock_uncertainty 0.25 [get_clocks clk]
set_clock_transition  0.15 [get_clocks clk]

# TT digital inputs (ui_in, rst_n). All of them are 2-FF synchronised in RTL (addr, rd, cfg_*, dbg, rst_n
# release), so they are asynchronous to clk on the board. They are still constrained (not false-pathed) so the
# first synchroniser flop sees a bounded on-chip path; 30 % of the period for the TT mux + pad path.
set tt_in [get_ports {ui_in[*] rst_n}]
set_input_delay -clock clk -max [expr 0.30 * $clk_period] $tt_in
set_input_delay -clock clk -min 0.0 $tt_in
set_input_transition 0.5 $tt_in

# Unused TT inputs (ena, uio_in) have no load inside the macro; constrain them so they are not reported as
# unconstrained, they time nothing.
set_input_delay -clock clk 0.0 [get_ports {ena uio_in[*]}]

# Comparator output (from C3 via C4). Captured with the s_tick enable on the clk edge that makes the bit clock
# fall (CL-23). The comparator is triggered by that same edge through C4, so comp_in changes AFTER the capture
# edge (min delay = clk -> fs_clk flop -> C4 phase gen -> comparator latch, several ns) and is stable for the
# rest of the fs period. Max delay is a full fs period minus margin; we budget it as one clk period (tightest
# reading, so the macro does not depend on the enable for setup). Min = 1.0 ns is the hold-side assumption that
# C4/C3 PEX must confirm (finding F-IF-1 in HARDENING.md).
set_input_delay -clock clk -max [expr 0.50 * $clk_period] [get_ports comp_in]
set_input_delay -clock clk -min 1.0 [get_ports comp_in]
set_input_transition 0.3 [get_ports comp_in]

# TT outputs: registered read bus (CL-21) and debug bus. Board budget 30 % of the period.
set tt_out [get_ports {uo_out[*] uio_out[*] uio_oe[*]}]
set_output_delay -clock clk -max [expr 0.30 * $clk_period] $tt_out
set_output_delay -clock clk -min 0.0 $tt_out
set_load 0.05 $tt_out

# Analog control outputs to C4 level shifters (fs <= 4 MHz, levels). Budget 50 % of a clk period; the real
# requirement is skew between them (they change on the same fs-cycle start edge), reported, not constrained.
set ana_out [get_ports {fs_clk rst_analog sys_swap ota_chop_phase short_o order_o boost_o trim_o[*] y_force bit_valid y_dac}]
set_output_delay -clock clk -max [expr 0.50 * $clk_period] $ana_out
set_output_delay -clock clk -min 0.0 $ana_out
set_load 0.02 $ana_out

set_max_transition 1.5 [current_design]
set_max_fanout 10 [current_design]
