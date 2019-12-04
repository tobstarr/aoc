defmodule Aoc.Y2019.D4 do
  use Aoc.Boilerplate,
    transform: fn raw ->
      [from, to] =
        raw
        |> String.split("-")
        |> Enum.map(&String.to_integer(&1))

      Range.new(from, to)
    end

  defguard never_decrease?(a, b, c, d, e, f)
           when a <= b and b <= c and c <= d and d <= e and e <= f

  defguard same_adjacent_digits?(a, b, c, d, e, f)
           when a == b or b == c or c == d or d == e or e == f

  def part1(input \\ processed()) do
    input
    |> Flow.from_enumerable()
    |> Flow.filter(&valid_password?(Integer.digits(&1)))
    |> Enum.count()
  end

  def part2(input \\ processed()) do
    input
    |> Flow.from_enumerable()
    |> Flow.filter(&valid_password?(Integer.digits(&1)))
    |> Flow.filter(&really_valid_password?(Integer.digits(&1)))
    |> Enum.count()
  end

  defp valid_password?([a, b, c, d, e, f])
       when never_decrease?(a, b, c, d, e, f) and same_adjacent_digits?(a, b, c, d, e, f) do
    true
  end

  defp valid_password?(_) do
    false
  end

  def really_valid_password?(digits) do
    digits
    |> make_sequence()
    |> Enum.find(fn {_k, v} -> v == 2 end)
  end

  def make_sequence(digits, previous \\ nil, sequence \\ %{})

  def make_sequence([], _previous, sequence), do: sequence

  def make_sequence([head | rest], previous, sequence) do
    case head == previous do
      true -> make_sequence(rest, head, Map.update(sequence, head, 2, &(&1 + 1)))
      false -> make_sequence(rest, head, sequence)
    end
  end
end
