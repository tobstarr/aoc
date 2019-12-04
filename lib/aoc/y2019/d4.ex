defmodule Aoc.Y2019.D4 do
  use Aoc.Boilerplate,
    transform: fn raw ->
      [from, to] =
        raw
        |> String.split("-")
        |> Enum.map(&String.to_integer(&1))

      Range.new(from, to) |> Flow.from_enumerable()
    end

  defguard never_decrease?(a, b, c, d, e, f)
           when a <= b and b <= c and c <= d and d <= e and e <= f

  defguard same_adjacent_digits?(a, b, c, d, e, f)
           when a == b or b == c or c == d or d == e or e == f

  defguard strict_adjacent_digits?(a, b, c, d, e, f)
           when (a == b and b != c) or
                  (a != b and b == c and c != d) or
                  (b != c and c == d and d != e) or
                  (c != d and d == e and e != f) or
                  (d != e and e == f)

  def part1(input \\ processed()) do
    input
    |> Flow.filter(&valid_password?(Integer.digits(&1)))
    |> Enum.count()
  end

  def part2(input \\ processed()) do
    input
    |> Flow.filter(&really_valid_password?(Integer.digits(&1)))
    |> Enum.count()
  end

  defp valid_password?([a, b, c, d, e, f])
       when never_decrease?(a, b, c, d, e, f) and
              same_adjacent_digits?(a, b, c, d, e, f) do
    true
  end

  defp valid_password?(_), do: false

  def really_valid_password?([a, b, c, d, e, f])
      when never_decrease?(a, b, c, d, e, f) and
             strict_adjacent_digits?(a, b, c, d, e, f) do
    true
  end

  def really_valid_password?(_), do: false
end
