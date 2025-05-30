import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

async def read(dut, address):
    dut._log.info(f"Sending read request to address: {address}")
    while dut.read_rdy.value != 1:
        await Timer(1, units='ns')
    dut.read_address.value = address
    dut.read_en.value = 1
    await RisingEdge(dut.CLK)
    response = dut.read_data.value
    dut._log.info(f"Received data: {response} from address: {address}")
    dut.read_en.value = 0
    return response

async def write(dut, address, data):
    dut._log.info(f"Sending write request to address: {address} with data: {data}")
    while dut.write_rdy.value != 1:
        await Timer(1, units='ns')
    dut.write_address.value = address
    dut.write_data.value = data
    dut.write_en.value = 1
    await RisingEdge(dut.CLK)
    dut.write_en.value = 0
    dut._log.info(f"Data: {data} written to address: {address}")
    pass

async def reset_seq(dut):
    dut.RST_N.value = 1
    await Timer(1, "ns")
    dut.RST_N.value = 0
    await Timer(1, "ns")
    await RisingEdge(dut.CLK)
    dut.RST_N.value = 1
    pass

async def check_fifo_status(dut, fifo_name):
    dut._log.info(f"Checking {fifo_name} FIFO status")
    if fifo_name == "A":
        status_address = 0x00
    elif fifo_name == "B":
        status_address = 0x01
    elif fifo_name == "Y":
        status_address = 0x02
    else:
        raise ValueError("Invalid FIFO name")

    status = await read(dut, status_address)
    if status == 1:
        dut._log.info(f"{fifo_name} FIFO is not full/empty")
    else:
        dut._log.info(f"{fifo_name} FIFO is full/empty")

async def write_testcase(dut, A, B):
    dut._log.info(f"Writing to FIFOs: A={A}, B={B}")
    #Check A FIFO status
    await check_fifo_status(dut, "A")
    await write(dut, 0x04, A)
    #Check B FIFO status
    await check_fifo_status(dut, "B")
    await write(dut, 0x05, B)
    #Check Y FIFO status
    await check_fifo_status(dut, "Y")
    # Read the output
    dut._log.info("Reading output from Y FIFO")
    output = await read(dut, 0x03)
    assert output == (A | B), f"Output mismatch: expected {A | B}, got {output}"

@cocotb.test()
async def dut_test(dut):
    dut._log.info("Starting DUT test")
    
    # Start clock and reset sequence
    dut.CLK.value = 0
    cocotb.start_soon(Clock(dut.CLK, 10, units="ns").start())
    await reset_seq(dut)
    dut._log.info("Reset complete, starting test sequence")

    A_possible = [0, 1]
    B_possible = [0, 1]

    for A in A_possible:
        for B in B_possible:
            dut._log.info(f"Testing with A={A}, B={B}")
            await write_testcase(dut, A, B)
            await Timer(10, units='ns')
    dut._log.info("DUT test completed successfully")