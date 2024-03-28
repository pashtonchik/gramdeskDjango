import turtle as t

k = 20

t.speed(20)

for i in range(4):
    t.forward(10 * k)

    t.right(60)

    t.forward(10 * k)

    t.right(120)

t.up()


for x in range(-10, 20):
    for y in range(-10, 4):
        t.goto(x * k, y * k)
        t.dot(3)



t.done()