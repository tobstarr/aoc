defmodule  Aoc.Y2019.D1 do
  use  Aoc.Boilerplate,
      transform: fn raw -> raw |> String.split() |> Enum.map(&String.to_integer(&1)) end
  
  def part1(input \\ processed()) do
    input
    |> Enum.reduce(0, fn mass, fuel ->
      fuel + needed_fuel(mass)
    end)
  end

  def part2(input \\ processed()) do
    input
    |> Enum.reduce(0, fn mass, fuel ->
      fuel + needed_fuel_recursive(mass)
    end)
  end

  defp needed_fuel_recursive(mass, total \\ 0)
  defp needed_fuel_recursive(mass, total) when mass <= 0, do: total

  defp needed_fuel_recursive(mass, total) do
    fuel = needed_fuel(mass)

    needed_fuel_recursive(fuel, total + fuel)
  end

  defp needed_fuel(mass) do
    (div(mass, 3) - 2)
    |> max(0)
  end
end