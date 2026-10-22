# Julia/MPSGE comparison, step 2: solve Phillipson's Julia port of Rutherford's MPSGE IFPRI model on the Philippine
# comparison SAM (built by Infinity GEM 0.3 validation/julia_mpsge/build_mpsge_inputs.py), unchanged model code.
# Usage: julia run_phl.jl <data folder> <output folder>
using Pkg
Pkg.activate(@__DIR__)
using IFPRI_model, MPSGE, JuMP, PATHSolver, DataFrames, CSV, Downloads

# PATH licence: the solver author's published evaluation licence (pages.cs.wisc.edu/~ferris/path/julia/LICENSE,
# valid to 31 Dec 2035), read at run time and not stored. Without it PATH stops at 300 variables.
page = String(take!(Downloads.download("https://pages.cs.wisc.edu/~ferris/path/julia/LICENSE", IOBuffer())))
lic = match(r"export PATH_LICENSE_STRING=\"([^\"]+)\"", page)
lic === nothing && error("PATH licence string not found on the published page")
ENV["PATH_LICENSE_STRING"] = lic.captures[1]

datadir, outdir = ARGS[1], ARGS[2]
mkpath(outdir)
data = load_data(datadir)
# government factor income (e.g. a capital tax): the loader creates an empty 'govt' row in fe0; fill it if supplied
gpath = joinpath(datadir, "fe0_govt.csv")
if isfile(gpath)
    for r in eachrow(CSV.read(gpath, DataFrame, stringtype = String))
        data[:fe0]["govt", r.f] = r.value
    end
end

function report(M, label)
    df = generate_report(M)
    df[!, :run] .= label
    return df
end

results = DataFrame[]
for (cname, flags) in (("savings_fixedGS", (flexiblePFX = 1, eqyield = 0, fixedGS = 1)),)
    M = IFPRI_mpsge(data; flags...)
    # benchmark: must replicate the SAM with no iterations
    solve!(M; cumulative_iteration_limit = 0)
    push!(results, report(M, "$(cname)|benchmark_check"))
    solve!(M)
    push!(results, report(M, "$(cname)|benchmark"))
    # experiment 1: abolish all tariffs (Rutherford's own experiment)
    set_value!.(M[:tm], 0.0)
    solve!(M)
    push!(results, report(M, "$(cname)|no_tariffs"))
end
out = vcat(results...; cols = :union)
CSV.write(joinpath(outdir, "mpsge_results.csv"), out)
println("written ", joinpath(outdir, "mpsge_results.csv"), " rows ", nrow(out))
println(first(out, 5))
