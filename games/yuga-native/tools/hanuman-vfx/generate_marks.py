"""Rasterize original Hanuman invocation masks in windup/release/impact columns."""
from __future__ import annotations

import argparse
from math import cos, pi, sin, tau
from pathlib import Path

from PIL import Image, ImageDraw

CELL = 128
SCALE = 3
CENTER = CELL * SCALE / 2
RANGE = CENTER * .91
KINDS = ("crescent", "ward", "wind", "ember", "mountain")


def polar(radius, angle, center=(0, 0)):
    return center[0] + radius * cos(angle), center[1] + radius * sin(angle)


class Ink:
    def __init__(self):
        self.layers = [Image.new("L", (CELL * SCALE, CELL * SCALE)) for _ in range(3)]
        self.pens = [ImageDraw.Draw(layer) for layer in self.layers]

    @staticmethod
    def plot(point):
        return CENTER + point[0] * RANGE, CENTER + point[1] * RANGE

    def line(self, points, weight=.022, channel=1, level=255):
        self.pens[channel].line([self.plot(point) for point in points], fill=level,
                                width=max(1, round(weight * RANGE)), joint="curve")

    def shape(self, points, level=108):
        self.pens[0].polygon([self.plot(point) for point in points], fill=level)

    def arc(self, radius, start=0.0, finish=tau, *, center=(0, 0), weight=.029, channel=1, level=255):
        self.line([polar(radius, start + i * (finish - start) / 80, center) for i in range(81)],
                  weight, channel, level)

    def leaf(self, tip, foot, width, fill=116):
        x, y = tip[0] - foot[0], tip[1] - foot[1]
        distance = (x*x + y*y) ** .5
        cross = (-y/distance, x/distance)
        bands = []
        for side in (-1, 1):
            bands.append([
                (foot[0] + t*x + side*cross[0]*width*sin(pi*t),
                 foot[1] + t*y + side*cross[1]*width*sin(pi*t))
                for t in (i/16 for i in range(17))])
        points = bands[0] + bands[1][::-1]
        self.shape(points, fill)
        self.line(points, .029)
        self.line([foot, (foot[0] + .74*x, foot[1] + .74*y)], .018, 2, 194)

    def render(self):
        return Image.merge("RGB", self.layers).resize((CELL, CELL), Image.Resampling.LANCZOS)


def solar(ink, stage):
    if stage == 1:
        # Side-lit crescent with a sculpted feathered trailing edge.
        arc = [polar(.88, -.16 - .88*pi*i/38, (0, .22)) for i in range(39)]
        edge = [polar(.88 - .27*sin(pi*i/38), -.16 - .88*pi*i/38, (0, .24)) for i in range(38, -1, -1)]
        ink.shape(arc + edge, 171)
        ink.line(arc, .062)
        ink.line(edge, .025, 2)
        for tick in range(1, 9):
            angle = -.16 - .88*pi*tick/10
            ink.line([polar(.62, angle + .07, (0, .23)), polar(.82, angle, (0, .23))], .035, 2)
        return
    radius = .31 if stage == 0 else .21
    ink.arc(radius, weight=.034)
    ink.arc(radius * .76, weight=.023, channel=2)
    for i in range(12):
        angle = i*tau/12 + (pi/12 if stage == 2 else 0)
        outer = radius + (.24 if stage == 0 else .53 if i % 3 == 0 else .28)
        ink.shape([polar(radius+.04, angle-.042), polar(outer, angle), polar(radius+.04, angle+.042)], 165)
        ink.line([polar(radius+.07, angle), polar(outer-.035, angle)], .029)
    if stage == 0:
        ink.arc(.76, .27, pi-.27, channel=2)
        ink.arc(.76, pi+.27, tau-.27, channel=2)


def ward(ink, stage):
    center = (0, .11 if stage == 1 else .02)
    petal_angle = (-pi*.68, -pi*.33, -pi*.50, -pi*.22, -pi*.78)
    length = .57 + .045*stage
    for i, angle in enumerate(petal_angle[:3 if stage == 0 else 5]):
        ink.leaf(polar(length*(1-.06*i), angle, center), center, .105*(1+.11*stage))
    ink.arc(.51 + .14*stage, .12, pi-.12, weight=.039, center=center, channel=2)
    if stage == 2:
        for angle in (0, pi/2, pi, 3*pi/2):
            p = polar(.78, angle, center)
            ink.line([p, polar(.87, angle, center)], .035)


def vault(ink, stage):
    shafts = (-.32, .32) if stage == 0 else (-.47, 0, .47) if stage == 1 else (-.30, .30)
    for i, x in enumerate(shafts):
        tip = (x*.58, -.66 + .15*(i % 2))
        heel = (x, .58 - .12*stage)
        ink.leaf(tip, heel, .105 + .017*stage, 102)
        for j in range(1, 5):
            t = j/6
            p = (heel[0]+t*(tip[0]-heel[0]), heel[1]+t*(tip[1]-heel[1]))
            ink.line([(p[0]-.10, p[1]+.06), p, (p[0]+.10, p[1]+.04)], .019, 2)
    if stage == 2:
        ink.line([(-.17, .47), (0, .25), (.17, .47)], .036)


def ember(ink, stage):
    count = 3 + stage * 2
    for t in (i/(count-1) for i in range(count)):
        x = (t-.5)*1.4
        y = -.62 + .51*abs(x)
        foot = (x*.19, .71- .07*stage)
        tip = (x, y - .055*stage)
        waviness = .095*sin(t*9 + stage*.8)
        pts = [(foot[0] + (tip[0]-foot[0])*q + waviness*sin(tau*q),
                foot[1] + (tip[1]-foot[1])*q) for q in (0,.18,.49,.68,1)]
        ink.line(pts,.07 if stage == 2 else .052,2,191)
        ink.line(pts,.027)
        if stage > 0:
            ink.shape([tip,(tip[0]-.067,tip[1]+.22),pts[-2],(tip[0]+.069,tip[1]+.18)],144)
    ink.arc(.34 + stage*.06, .18, pi-.18, center=(0,.28), weight=.022, channel=2)


def mountain(ink, stage):
    face = [(-.76,.41),(-.46,.12),(-.22,.20),(.13,-.46),(.42,-.08),(.70,.22),(.77,.41)]
    if stage > 0:
        ink.shape(face + [(.22,.59),(-.35,.55)], 92 + 24*stage)
        ink.line(face, .043)
        ink.line([(.13,-.46),(.22,.10),(.02,.22),(.22,.59)], .031, 2)
        ink.line([(-.22,.20),(-.46,.35),(-.35,.55)], .025, 2)
    for factor in (.82,.64,.45) if stage == 0 else (.90,.76):
        points = [(x*factor*(1+.043*sin(i*1.9)), y*factor*.74)
                  for i, (x,y) in enumerate(polar(1, tau*j/32) for j in range(33))]
        ink.line(points, .025 if stage == 0 else .019, 1 if stage == 0 else 2)
    if stage == 0:
        ink.shape([(-.16,.10),(0,-.19),(.16,.10)], 139)
        ink.line([(-.16,.10),(0,-.19),(.16,.10)], .029)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    atlas = Image.new("RGB", (CELL*3, CELL*len(KINDS)))
    for row, painter in enumerate((solar, ward, vault, ember, mountain)):
        for stage in range(3):
            ink = Ink()
            painter(ink, stage)
            atlas.paste(ink.render(), (stage*CELL, row*CELL))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(args.output, optimize=True)


if __name__ == "__main__":
    main()
