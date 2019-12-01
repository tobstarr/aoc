defmodule Day1 do
  def file_stream(path) do
    path
    |> File.stream!()
    |> Stream.map(&String.trim(&1))
    |> Stream.map(&String.to_integer(&1))
  end

  def part1(file_path) do
    file_path
    |> file_stream()
    |> Stream.map(&needed_fuel/1)
    |> Enum.sum()
  end

  def part2(file_path) do
    file_path
    |> file_stream()
    |> Stream.map(&total_fuel/1)
    |> Enum.sum()
  end

  defp total_fuel(mass, total \\ 0)
  defp total_fuel(mass, total) when mass <= 0, do: total

  defp total_fuel(mass, total) do
    fuel = needed_fuel(mass)

    total_fuel(fuel, total + fuel)
  end

  defp needed_fuel(mass) do
    (div(mass, 3) - 2)
    |> max(0)
  end
end
