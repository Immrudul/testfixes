# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer

# Sine LUT values
SINE_VALUES_TABLE = {
    0: 50,
    1: 40,
    2: 30,
    3: 20,
    4: 10,
    5: 0,
    6: 10,
    7: 20,
    8: 30,
    9: 40
}

# Expected "U" shape
expected_U = [
    [1,1,1,0,0,0,0,0,1,1,1],
    [1,1,1,0,0,0,0,0,1,1,1],
    [1,1,1,0,0,0,0,0,1,1,1],
    [1,1,1,0,0,0,0,0,1,1,1],
    [1,1,1,0,0,0,0,0,1,1,1],
    [1,1,1,0,0,0,0,0,1,1,1],
    [1,1,1,0,0,0,0,0,1,1,1],
    [1,1,1,0,0,0,0,0,1,1,1],
    [1,1,1,0,0,0,0,0,1,1,1],
    [1,1,1,0,0,0,0,0,1,1,1],
    [1,1,1,0,0,0,0,0,1,1,1],
    [1,1,1,0,0,0,0,0,1,1,1],
    [1,1,1,0,0,0,0,0,1,1,1],
    [0,1,1,0,0,0,0,0,1,1,0],
    [0,0,1,1,0,0,0,1,1,0,0],
    [0,0,0,1,1,1,1,1,0,0,0]
]

# Expected static top line
expected_static_top_line = [
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

# ---------------- Clock and reset setup ----------------
@cocotb.test()
async def test_setup(dut):
    dut._log.info("Starting setup...")

    # Start clock at 25 MHz (20 ns period)
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())

    # Reset
    dut.rst_n.value = 0
    await Timer(40, units="ns")
    dut.rst_n.value = 1
    await Timer(20, units="ns")

    dut._log.info("RESET DONE")

# ---------------- Static top line test ----------------
@cocotb.test()
async def test_static_top_line(dut):
    dut._log.info("Testing static top line...")

    height = len(expected_static_top_line)
    width  = len(expected_static_top_line[0])

    for y in range(10, height*8):
        for x in range(250, width*8):
            dut.pix_x_sim.value = x
            dut.pix_y_sim.value = y
            await Timer(1, units="ns")

            actual = bool(dut.draw_line_sim.value)
            expected = bool(expected_static_top_line[y//8][x//8])

            assert actual == expected, f"Static top line fail at ({x},{y}): got {actual}, expected {expected}"

    dut._log.info("static_top_line passed")

# ---------------- "U" helper ----------------
async def u_shape_helper(dut, x_coord, y_coord, isUW):
    height = len(expected_U)
    width  = len(expected_U[0])

    dut.x_pos_sim.value = x_coord
    dut.y_pos_sim.value = y_coord

    for y in range(height):
        for x in range(width):
            dut.pix_x_sim.value = x_coord - 5 + x
            dut.pix_y_sim.value = y_coord - 10 + y
            await Timer(1, units="ns")

            actual = bool(dut.draw_player_sim.value) if isUW else bool(dut.draw_U_sim.value)
            expected = bool(expected_U[y][x])

            assert actual == expected, f"U shape fail at ({x},{y}): got {actual}, expected {expected}"

# ---------------- Player test ----------------
@cocotb.test()
async def test_player(dut):
    dut._log.info("Start player test")

    x_coord = 200
    y_coord = 100
    await u_shape_helper(dut, x_coord, y_coord, True)
    dut._log.info("Passed 1 U")

    x_coord += 17
    await u_shape_helper(dut, x_coord, y_coord, True)
    dut._log.info("Passed 2 U")

    x_coord += 10
    await u_shape_helper(dut, x_coord, y_coord, True)
    dut._log.info("Passed 3 U")

    dut._log.info("player passed")

# ---------------- U shape test ----------------
@cocotb.test()
async def test_U_shape(dut):
    dut._log.info("Start U_shape test")
    await u_shape_helper(dut, 100, 100, False)
    dut._log.info("U_shape passed")

# ---------------- Double sine wave test ----------------
TOP_X        = 100
TOP_Y        = 180
BOTTOM_X     = 540
BOTTOM_Y     = 400
BAR_WIDTH    = 40
VISIBLE_WIDTH= 25
HEIGHT       = 60

@cocotb.test()
async def test_double_sin(dut):
    dut._log.info("Start double_sin test")

    for x_offset in range(0, 400, 20):
        for pix_x in range(TOP_X+1, BOTTOM_X):
            for pix_y in range(TOP_Y+1, BOTTOM_Y):
                sin_height = SINE_VALUES_TABLE[((pix_x + x_offset)//BAR_WIDTH) % 10]
                correct_y_pos = (TOP_Y + 50 - sin_height + HEIGHT > pix_y) or (pix_y > BOTTOM_Y - sin_height - HEIGHT)
                correct_x_pos = (pix_x + x_offset) % BAR_WIDTH < VISIBLE_WIDTH

                dut.pix_x_sim.value = pix_x
                dut.pix_y_sim.value = pix_y
                dut.x_offset_sim.value = x_offset
                await Timer(1, units="ns")

                actual = bool(dut.draw_double_sin_sim.value)
                expected = correct_y_pos and correct_x_pos

                assert actual == expected, f"Double sin fail at ({pix_x},{pix_y}) offset {x_offset}: got {actual}, expected {expected}"

    dut._log.info("double_sin passed")

# ---------------- Sine LUT test ----------------
@cocotb.test()
async def test_sine_lut(dut):
    dut._log.info("Start sine_lut test")

    for index, value in SINE_VALUES_TABLE.items():
        dut.tb_pos_sim.value = index
        await Timer(1, units="ns")
        actual = int(dut.tb_sin_output_sim.value)
        dut._log.info(f"pos={index} → sin_output={actual}, value={value}")
        assert actual == value, f"Sine LUT fail at index {index}: got {actual}, expected {value}"

    dut._log.info("sine_lut passed")
