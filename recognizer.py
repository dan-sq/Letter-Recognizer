import math

def degrees_to_radians(degrees):
    return degrees * math.pi / 180

N = 96
SIZE = 250
PARTIAL_DIFFERENTIAL = 0.30
ORIGIN = (0, 0)
INDEX = 12
ANGLE_SIMILARITY_THRESHOLD = degrees_to_radians(30)
ANGLE_RANGE = degrees_to_radians(45)
ANGLE_PRECISION = degrees_to_radians(2)
PHI = (-1.0 + math.sqrt(5.0)) * 0.5

class Unistroke:
    def __init__(self, points, bounded_rotation_invariance):
        points = resample(points, N)
        omega = indicative_angle(points)
        points = rotate_by(points, -omega)
        points = scale_dim_to(points, SIZE)

        if bounded_rotation_invariance:
            points = rotate_by(points, omega)

        points = translate_to(points, ORIGIN)

        self.points = points
        self.start_unit_vector = calc_start_unit_vector(points, INDEX)

class Multistroke:
    def __init__(self, name, strokes, bounded_rotation_invariance=True):
        self.name = name
        self.n_strokes = len(strokes)
        self.unistrokes = []

        order, orders = [], []

        for i in range(len(strokes)):
            order.append(i)
        
        heap_permute(len(strokes), order, orders)

        for points in make_unistrokes(strokes, orders):
            self.unistrokes.append(Unistroke(points, bounded_rotation_invariance))

def heap_permute(n, order, orders):
    if n == 1:
        orders.append(order[:])
    else:
        for i in range(n):
            heap_permute(n - 1, order, orders)
            if n % 2 == 1:
                temp = order[0]
                order[0] = order[n - 1]
                order[n - 1] = temp
            else:
                temp = order[i]
                order[i] = order[n - 1]
                order[n - 1] = temp

def make_unistrokes(strokes, orders):
    unistrokes = []

    for r in range(len(orders)):
        for b in range(2 ** len(orders[r])):
            unistroke = []
            for i in range(len(orders[r])):
                if (b >> i) & 1:
                    stroke = strokes[orders[r][i]][::-1]
                else:
                    stroke = strokes[orders[r][i]]

                unistroke.extend(stroke)

            unistrokes.append(unistroke)

    return unistrokes

def combine_strokes(strokes):
    points = []

    for i in range(len(strokes)):
        for j in range(len(strokes[i])):
            points.append(strokes[i][j])

    return points

def resample(points, n):
    points = points[:]
    interval = path_length(points) / (n - 1)
    d = 0
    new_points = [points[0]]

    i = 1
    while i < len(points):
        dist = distance(points[i - 1], points[i])
        if dist == 0:
            i += 1
            continue
        
        if ((d + dist) >= interval):
            x1, y1 = points[i - 1]
            x2, y2 = points[i]

            qx = x1 + ((interval - d) / dist) * (x2 - x1)
            qy = y1 + ((interval - d) / dist) * (y2 - y1)

            new_points.append((qx, qy))
            points.insert(i, (qx, qy))

            d = 0
        else:
            d += dist

        i += 1

    if len(new_points) == n - 1:
        new_points.append(points[-1])

    return new_points

def path_length(points):
    d = 0

    for i in range(1, len(points)):
        d += distance(points[i - 1], points[i])

    return d

def distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    dx = x2 - x1
    dy = y2 - y1

    return math.sqrt(dx * dx + dy * dy)

def indicative_angle(points):
    cx, cy = centroid(points)
    start_x, start_y = points[0]

    return math.atan2(cy - start_y, cx - start_x)

def centroid(points):
    x, y = 0.0, 0.0

    for i in range(len(points)):
        px, py = points[i]
        x += px
        y += py

    x = x / len(points)
    y = y / len(points)

    return (x, y)

def rotate_by(points, omega):
    cx, cy = centroid(points)
    new_points = []

    for p in points:
        px, py = p
        qx = (px - cx) * math.cos(omega) - (py - cy) * math.sin(omega) + cx
        qy = (px - cx) * math.sin(omega) + (py - cy) * math.cos(omega) + cy

        new_points.append((qx, qy))

    return new_points

def scale_dim_to(points, size):
    new_points = []
    bw, bh = bounding_box(points)

    if bw == 0:
        bw = 1

    if bh == 0:
        bh = 1

    for p in points:
        px, py = p

        if min(bw / bh, bh / bw) <= PARTIAL_DIFFERENTIAL:
            qx = px * size / max(bw, bh)
            qy = py * size / max(bw, bh)
        else:
            qx = px * size / bw
            qy = py * size / bh

        new_points.append((qx, qy))

    return new_points

def bounding_box(points):
    min_x, max_x, min_y, max_y = math.inf, -math.inf, math.inf, -math.inf

    for p in points:
        px, py = p

        min_x = min(min_x, px)
        min_y = min(min_y, py)
        max_x = max(max_x, px)
        max_y = max(max_y, py)

    return (max_x - min_x, max_y - min_y)

def translate_to(points, k):
    cx, cy = centroid(points)
    kx, ky = k
    new_points = []

    for p in points:
        px, py = p
        qx = px + kx - cx
        qy = py + ky - cy

        new_points.append((qx, qy))

    return new_points

def calc_start_unit_vector(points, i):
    start_px, start_py = points[0]
    i_px, i_py = points[i]

    qx = i_px - start_px
    qy = i_py - start_py

    length = math.sqrt(qx * qx + qy * qy)

    if length == 0:
        return (0, 0)

    vx = qx / length
    vy = qy / length

    return (vx, vy)

def recognize(strokes, multistrokes, bounded_rotation_invariance=True):
    candidate = Unistroke(combine_strokes(strokes), bounded_rotation_invariance)
    b = math.inf
    name = None

    for m in multistrokes:
        #if len(strokes) != m.n_strokes:
        #    continue

        for u in m.unistrokes:
            if (angle_between_vectors(candidate.start_unit_vector, u.start_unit_vector) <= ANGLE_SIMILARITY_THRESHOLD):
                d = distance_at_best_angle(candidate.points, u.points, -ANGLE_RANGE, ANGLE_RANGE, ANGLE_PRECISION)

                if d < b:
                    b = d
                    name = m.name

    if name is None:
        return None, 0

    score = 1 - b / (0.5 * math.sqrt(SIZE * SIZE + SIZE * SIZE))

    return name, score

def angle_between_vectors(a, b):
    ax, ay = a
    bx, by = b

    n = ax * bx + ay * by
    c = max(-1.0, min(1.0, n))

    return math.acos(c)

def distance_at_best_angle(points, t, theta_a, theta_b, delta_theta):
    x1 = PHI * theta_a + (1.0 - PHI) * theta_b
    f1 = distance_at_angle(points, t, x1)

    x2 = (1.0 - PHI) * theta_a + PHI * theta_b
    f2 = distance_at_angle(points, t, x2)

    while(abs(theta_b - theta_a) > delta_theta):
        if f1 < f2:
            theta_b = x2
            x2 = x1
            f2 = f1
            x1 = PHI * theta_a + (1.0 - PHI) * theta_b
            f1 = distance_at_angle(points, t, x1)
        else:
            theta_a = x1
            x1 = x2
            f1 = f2
            x2 = (1.0 - PHI) * theta_a + PHI * theta_b
            f2 = distance_at_angle(points, t, x2)

    return min(f1, f2)

def distance_at_angle(points, t, theta):
    new_points = rotate_by(points, theta)
    d = path_distance(new_points, t)

    return d

def path_distance(a, b):
    d = 0

    for i in range(len(a)):
        d += distance(a[i], b[i])

    return d / len(a)