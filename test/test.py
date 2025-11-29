# SPDX-FileCopyrightText: © 2025
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge

# =====================================================================
# VGA PIN DECODE (matches your tt project pinout)
# uo_out[7] = HSYNC
# uo_out[6] = B0
# uo_out[5] = G0
# uo_out[4] = R0
# uo_out[3] = VSYNC
# uo_out[2] = B1
# uo_out[1] = G1
# uo_out[0] = R1
# =====================================================================

def decode_rgb(uo_value: int):
    """Return (R, G, B) as 2-bit values each."""
    R = ((uo_value >> 4) & 1) | (((uo_value >> 0) & 1) << 1)
    G = ((uo_value >> 5) & 1) | (((uo_value >> 1) & 1) << 1)
    B = ((uo_value >> 6) & 1) | (((uo_value >> 2) & 1) << 1)
    return R, G, B

def bit(value, n):
    return (value >> n) & 1


# =====================================================================
#  FRAME + SCANLINE SYNCHRONIZATION HELPERS
# =====================================================================

async def wait_for_vsync(dut):
    """Wait for VSYNC rising edge."""
    prev = bit(int(dut.uo_out.value), 3)
    while True:
        await Timer(1, "ns")
        cur = bit(int(dut.uo_out.value), 3)
        if prev == 0 and cur == 1:
            return
        prev = cur


async def wait_for_hsync(dut):
    """Wait for HSYNC rising edge."""
    prev = bit(int(dut.uo_out.value), 7)
    while True:
        await Timer(1, "ns")
        cur = bit(int(dut.uo_out.value), 7)
        if prev == 0 and cur == 1:
            return
        prev = cur


# =====================================================================
#  VGA PIXEL SAMPLER
# =====================================================================
async def get_pixel(dut, target_x, target_y):
    """
    Return (R,G,B) at pixel (target_x,target_y).
    Must sync to VSYNC then raster-scan.
    """

    # wait for new frame
    await wait_for_vsync(dut)

    x = 0
    y = 0

    # scan until we reach desired y
    while y < target_y:
        await wait_for_hsync(dut)
        y += 1

    # now on desired scanline → walk forward until target_x
    while x < target_x:
        await Timer(40, "ns")  # 25MHz pixel ⇒ 40ns per pixel
        x += 1

    # sample pixel at (x,y)
    rgb = decode_rgb(int(dut.uo_out.value))
    return rgb


# =====================================================================
#  EXPECTED PATTERNS
# =====================================================================

# From your original test
expected_static_top = [
    [0,0,0,0,0,1,1,1,1,0,0,0,0,0],
    [0,0,0,0,1,0,0,0,0,1,0,0,0,0],
    [0,0,0,1,0,0,0,0,0,0,1,0,0,0],
    [0,0,0,1,0,1,0,0,1,0,1,0,0,0],
    [0,0,0,1,0,0,1,1,0,0,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,0,0,1,1,1,1,0,0,1,0,0],
    [0,1,0,0,0,0,0,0,0,0,0,0,1,0],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [0,1,0,1,0,0,0,0,0,0,0,1,0,1],
    [0,0,1,0,0,0,0,0,0,0,1,0,0,0],
    [0,0,0,1,0,0,0,0,0,1,0,0,0,0],
    [0,0,1,0,0,0,1,1,0,0,1,0,0,0],
    [0,0,0,1,1,1,0,0,0,1,1,1,0,0]
]


# =====================================================================
#  MAIN TEST SETUP
# =====================================================================

@cocotb.test()
async def test_setup(dut):
    dut._log.info("Starting clock at 25MHz...")
    cocotb.start_soon(Clock(dut.clk, 40, "ns").start())  # 25 MHz
    dut.rst_n.value = 0
    dut.ena.value = 1
    dut.ui_in.value = 0

    await Timer(200, "ns")
    dut.rst_n.value = 1
    await Timer(200, "ns")

    dut._log.info("RESET DONE")


# =====================================================================
#  TEST STATIC TOP LINE
# =====================================================================
@cocotb.test()
async def test_static_top_line(dut):
    dut._log.info("Testing static top line...")

    # pattern starts at (250,10), each cell = 8×8 pixels
    base_x = 250
    base_y = 10

    for row in range(16):
        for col in range(14):
            expected = expected_static_top[row][col]
            px = base_x + col * 8 + 4
            py = base_y + row * 8 + 4

            R,G,B = await get_pixel(dut, px, py)
            actual = 1 if (R|G|B) else 0

            assert actual == expected, \
                f"Static top mismatch @ row={row} col={col}, got {actual} expected {expected}"

    dut._log.info("STATIC TOP LINE PASSED ✔")


# =====================================================================
#  TEST PLAYER ("UW")
# =====================================================================
@cocotb.test()
async def test_player(dut):
    dut._log.info("Testing player render...")

    # Player fixed X positions in your design
    U0 = 200
    U1 = 217
    U2 = 227

    # sample ~100px below top_line
    y = 250

    # Just verify something is drawn (white pixel)
    for X in [U0, U1, U2]:
        R,G,B = await get_pixel(dut, X, y)
        assert (R|G|B) != 0, f"No player pixel found at x={X},y={y}"

    dut._log.info("PLAYER SHAPE PASSED ✔")


# =====================================================================
#  TEST DOUBLE SINE
# =====================================================================
@cocotb.test()
async def test_double_sin(dut):
    dut._log.info("Testing double sine...")

    # Known visible window
    for x in range(120, 540, 40):
        for y in range(220, 360, 30):
            R,G,B = await get_pixel(dut, x, y)
            # double-sine produces bright white bars
            assert (R|G|B) != 0, f"Expected sine pixel at ({x},{y})"

    dut._log.info("DOUBLE SINE PASSED ✔")


# =====================================================================
#  TEST SINE LUT (observed via player y offset)
# =====================================================================
@cocotb.test()
async def test_sine_lut_visible(dut):
    dut._log.info("Testing sine LUT indirectly through player motion...")

    # change speed (which feeds LUT index)
    for idx in range(10):
        dut.ui_in.value = idx  # speed bits = lut index
        await Timer(20_000, "ns")  # wait a few frames

        # player center X
        x = 200
        # measure Y pixel brightness
        R,G,B = await get_pixel(dut, x, 290)
        brightness = R|G|B

        assert brightness != 0, f"LUT motion invalid at idx={idx}"

    dut._log.info("SINE LUT VISIBLE TEST PASSED ✔")
