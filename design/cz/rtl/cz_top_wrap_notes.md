# cz slot-level wrapper notes (D102)

Status: RTL written, not linted or simulated.

## Connection

```
 pins ui/uio -> addr_i[2:0], rd_i, dbg_i, bsel          spi_en, spi_sck, spi_cs_n
                   |                                         |
                   v                                         v
              +-----------------------  cz_spi  ------------------------+
              | spi_en=0: pass-through     spi_en=1: FSM drives addr_o/rd_o, dbg_o=0, data_o={0,MISO}
              +--addr_o,rd_o,dbg_o--> C9 (tt_um_sd_adc_c9 ui_in[2:0], ui_in[3], ui_in[7])
 C9 {uo_out,uio_out} = bus[15:0] --+--> cz_spi.bus (word capture)
                                   +--> cz_bus8(bus, bsel) -> data[7:0] -> cz_spi.data_in --> cz_spi.data_o -> data pins
```

C9 and cz_bus8 are unchanged. cz_spi is combinational on the pass-through path only (muxes), so with spi_en = 0 the
slot behaves as before D102. ui_in[6:4] (cfg pins) are not touched by cz_spi and keep their own wiring; the C9
`ui_in` word is {dbg_o, cfg pins[6:4], rd_o, addr_o[2:0]} (ui_in[3] = rd, ui_in[2:0] = addr, ui_in[7] = dbg).

## Pin map (cz_spi ports)

| port | dir | meaning |
|---|---|---|
| clk, rst_n | in | C9 clk, async reset |
| spi_en | in | static; 1 = SPI mode; changes only while spi_cs_n high |
| spi_sck, spi_cs_n | in | SPI mode 0 clock and chip select (active low) |
| addr_i[2:0], rd_i, dbg_i | in | external C9 read-port pins (ignored when spi_en = 1) |
| bus[15:0] | in | C9 {uo_out, uio_out}, dbg = 0 in SPI mode |
| data_in[7:0] | in | cz_bus8 output |
| addr_o[2:0], rd_o, dbg_o | out | to C9 ui_in[2:0], [3], [7] |
| data_o[7:0] | out | to data pins; spi_en = 1: data_o[0] = MISO, rest 0 |

Pin allocation of spi_en/spi_sck/spi_cs_n/bsel to the slot's ui/uio pins is not decided here (see questions).

## Timing

CS_n fall to snap_valid: <= 15 clk typical worst, <= 26 clk with one retake; host rule CS_n setup >= 32 clk.
CS_n high >= 8 clk. SCLK domain: MISO changes after SCLK falling edge; bit 95 present before the first rising edge.
Details are in the header of cz_spi.v.

## Open questions

1. The ui/uio pin assignment for spi_en, spi_sck, spi_cs_n and MISO (data[0]) in the slot, and the direction of the
   shared pins (uio_oe in tt_um_sd_adc_c9 is 8'hFF, outputs always on; the SPI inputs must come from ui pins or
   from uio pins with a changed uio_oe, which is outside the frozen C9 top).
2. Whether TT's pad/crossbar allows a clock-like input (spi_sck) on an ordinary ui pin with the 12 MHz SCLK limit
   (to be confirmed post-layout); spi_sck also drives async-reset-free flops only, so SDC needs a generated/async
   clock group for spi_sck vs clk.
3. SDC/STA: paths spi_cs_n -> clk flops (2-FF sync, set_false_path on the first stage), snap_valid and snapshot
   registers -> MISO (async to SCLK, static by protocol), rcnt/ptr async reset from cs_n.
4. A frame loaded between the status sample and C9's rd guard can still be cleared unread (about 5 clk window,
   C9 frozen); the frame counter gap tells the host. Accept, or add a final tag re-read before ack (+4 clk).
5. spi_en = 1 with external SCLK toggling while CS_n high: ignored by design (rcnt/ptr held in reset).
6. Is dbg_o forced 0 enough, or must the debug bus be reachable in SPI mode for bring-up? (Currently no.)
7. Assumes bus is {uo_out, uio_out} exactly as in c9_core; cz_bus8's bus input is the same 16 bits.

## DRDY and status pins in SPI mode (review SA-SPI-3, 2026-11-24)
- frame_ready and overrun are wired from C9 straight to their own two slot test outputs, never through cz_spi. They therefore stay live whatever spi_en is, and frame_ready is the host's DRDY line in SPI mode. The slot top must keep this wiring.
- A re-read (a new CS_n fall on a frame already acknowledged) pulses rd again. This is harmless: the C9 counter guard ignores it. It is also consistent with the spec: no ack is sent until the next CS_n fall, and a re-read is a new fall. The testbench default allows it; `+STRICT_ONE_ACK` stays an optional check.
- A re-read returns the same frame, except that status[15:14] change after the first ack. If a new frame loaded in between, the re-read returns the new frame.
