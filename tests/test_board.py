from balance_board import BalanceBoard


def board():
    b = BalanceBoard()
    b.calib = [[0] * 4, [1000] * 4, [2000] * 4]  # 0 kg, 17 kg, 34 kg per sensore
    return b


def pack(tr, br, tl, bl):
    out = []
    for v in (tr, br, tl, bl):
        out += [v >> 8, v & 0xFF]
    return out


def test_calibration_points():
    b = board()
    assert b._to_kg(0, 0) == 0
    assert abs(b._to_kg(1000, 0) - 17) < 1e-9
    assert abs(b._to_kg(2000, 0) - 34) < 1e-9


def test_interpolation_between_points():
    b = board()
    assert abs(b._to_kg(500, 0) - 8.5) < 1e-9
    assert abs(b._to_kg(1500, 0) - 25.5) < 1e-9


def test_total_weight_is_sum_of_sensors():
    b = board()
    b._on_data(pack(1000, 1000, 1000, 1000))
    assert abs(b.total - 68) < 1e-6


def test_center_of_gravity_directions():
    b = board()
    b._on_data(pack(2000, 2000, 500, 500))  # carico a destra
    assert b.cog[0] > 50
    b._on_data(pack(500, 500, 2000, 2000))  # carico a sinistra
    assert b.cog[0] < -50
    b._on_data(pack(2000, 500, 2000, 500))  # carico davanti (TR+TL)
    assert b.cog[1] > 30
    b._on_data(pack(500, 2000, 500, 2000))  # carico dietro
    assert b.cog[1] < -30


def test_centered_load_gives_zero_cog():
    b = board()
    b._on_data(pack(1000, 1000, 1000, 1000))
    assert abs(b.cog[0]) < 1e-6 and abs(b.cog[1]) < 1e-6


def test_no_data_before_calibration():
    b = BalanceBoard()
    b._on_data(pack(1000, 1000, 1000, 1000))  # non deve sollevare eccezioni
    assert b.total == 0.0


def test_not_healthy_when_closed():
    assert not BalanceBoard().healthy
