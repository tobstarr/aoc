defmodule Aoc.Y2019.D3 do
  use Aoc.Boilerplate,
    transform: fn raw ->
      raw
      |> String.split("\n")
      |> Enum.map(&String.split(&1, ","))
    end

  def part1(input \\ processed()) do
    input
  end

  def part2(input \\ processed()) do
  end
end
