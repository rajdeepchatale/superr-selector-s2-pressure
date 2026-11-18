"""Quick review fixes, 18 Nov evening.
Slide 20 (limits): Hendricks has no IPL games in the data (slide 23 says T20Is only),
so 'almost all T20Is' was wrong for him."""
import pathlib
p = pathlib.Path(__file__).resolve().parents[1] / "deck/project/slides/limits.html"
s = p.read_text(encoding="utf-8")
old = "Hendricks and Mujeeb are almost all T20Is, and Narine and Krunal are IPL only."
new = "Hendricks is all T20Is and Mujeeb nearly so, while Narine and Krunal are IPL only."
assert s.count(old) == 1, "text not found"
p.write_text(s.replace(old, new), encoding="utf-8")
print("slide 20 fixed")
