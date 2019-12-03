defmodule Aoc.Y2019.D3 do
  use Aoc.Boilerplate,
    transform: fn raw ->
      raw
      |> String.split("\n")
      |> Enum.map(&String.split(&1, ","))
    end

  def part1(input \\ processed()) do
    input
    |> Enum.with_index()
    |> Enum.reduce(%{}, fn {instructions, i}, grid ->
      calculate_grid(grid, instructions, i)
    end)
    |> get_points_with_intersections()
    |> Enum.reduce(:infinity, fn {x, y}, closest_distance ->
      md = manhattan_distance({0, 0}, {x, y})

      cond do
        closest_distance > md -> md
        true -> closest_distance
      end
    end)
  end

  def part2(_input \\ processed()) do
  end

  defp calculate_grid(grid, instructions, wire_id) do
    instructions
    |> Enum.reduce({grid, {0, 0}}, fn instruction, {grid, current_point} ->
      instruction
      |> parse_instruction()
      |> follow_wire(grid, current_point, wire_id)
    end)
    |> elem(0)
  end

  defp parse_instruction(instruction) do
    [direction, distance] =
      String.split(instruction, ~r{U|D|L|R}, include_captures: true, trim: true)

    {direction, String.to_integer(distance)}
  end

  defp follow_wire({"U", distance}, grid, {x, y}, wire_id) do
    grid =
      Enum.reduce((y + 1)..(y + distance), grid, fn new_y, grid ->
        Map.update(grid, {x, new_y}, [wire_id], &[wire_id | &1])
      end)

    {grid, {x, y + distance}}
  end

  defp follow_wire({"D", distance}, grid, {x, y}, wire_id) do
    grid =
      Enum.reduce((y - 1)..(y - distance), grid, fn new_y, grid ->
        Map.update(grid, {x, new_y}, [wire_id], &[wire_id | &1])
      end)

    {grid, {x, y - distance}}
  end

  defp follow_wire({"L", distance}, grid, {x, y}, wire_id) do
    grid =
      Enum.reduce((x - 1)..(x - distance), grid, fn new_x, grid ->
        Map.update(grid, {new_x, y}, [wire_id], &[wire_id | &1])
      end)

    {grid, {x - distance, y}}
  end

  defp follow_wire({"R", distance}, grid, {x, y}, wire_id) do
    grid =
      Enum.reduce((x + 1)..(x + distance), grid, fn new_x, grid ->
        Map.update(grid, {new_x, y}, [wire_id], &[wire_id | &1])
      end)

    {grid, {x + distance, y}}
  end

  defp get_points_with_intersections(grid) do
    grid
    |> Enum.reduce([], fn {point, intersections}, list ->
      case Enum.uniq(intersections) do
        [1, 0] -> [point | list]
        _ -> list
      end
    end)
  end

  defp manhattan_distance({x1, y1}, {x2, y2}) do
    abs(x1 - x2) + abs(y1 - y2)
  end
end
