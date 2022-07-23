within FMI.FMI2;
function FMI2SetContinuousStates
    input ExternalFMU instance;
    input Real x[nx];
    input Integer nx;
    external"C" FMU_FMI2SetContinuousStates(instance, x, nx) annotation (Library="ModelicaFMI");
end FMI2SetContinuousStates;
