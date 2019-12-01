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
    |> Stream.map(fn mass ->
      div(mass, 3) - 2
    end)
    |> Enum.sum()
  end

  def part2(file_path) do
    file_path
    |> file_stream()
    |> Stream.map(&calculate_fuel/1)
    |> Enum.sum()
  end

  def calculate_fuel(mass) do
    do_calculate_mass(mass, [])
  end

  def do_calculate_mass(mass, acc) when mass <= 0, do: Enum.sum(acc)

  def do_calculate_mass(mass, acc) do
    new_mass =
      (div(mass, 3) - 2)
      |> max(0)

    do_calculate_mass(new_mass, [new_mass | acc])
  end
end
