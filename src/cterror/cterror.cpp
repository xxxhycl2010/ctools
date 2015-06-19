/***************************************************************************
 *                   cterror - Parameter error calculation tool            *
 * ----------------------------------------------------------------------- *
 *  copyright (C) 2015 by Florent Forest                                   *
 * ----------------------------------------------------------------------- *
 *                                                                         *
 *  This program is free software: you can redistribute it and/or modify   *
 *  it under the terms of the GNU General Public License as published by   *
 *  the Free Software Foundation, either version 3 of the License, or      *
 *  (at your option) any later version.                                    *
 *                                                                         *
 *  This program is distributed in the hope that it will be useful,        *
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of         *
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
 *  GNU General Public License for more details.                           *
 *                                                                         *
 *  You should have received a copy of the GNU General Public License      *
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.  *
 *                                                                         *
 ***************************************************************************/
/**
 * @file cterror.cpp
 * @brief Parameter error calculation tool interface implementation
 * @author Florent Forest
 */

/* __ Includes ___________________________________________________________ */
#ifdef HAVE_CONFIG_H
#include <config.h>
#endif
#include <iostream>
#include "cterror.hpp"
#include "GTools.hpp"
#include "GOptimizer.hpp"

/* __ Method name definitions ____________________________________________ */
#define G_GET_PARAMETERS                         "cterror::get_parameters()"
#define G_ERR_BISECTION         "cterror::error_bisection(double&, double&)"
#define G_EVALUATE                              "cterror::evaluate(double&)"
#define G_RUN                                               "cterror::run()"

/* __ Debug definitions __________________________________________________ */

/* __ Coding definitions _________________________________________________ */


/*==========================================================================
 =                                                                         =
 =                        Constructors/destructors                         =
 =                                                                         =
 ==========================================================================*/

/***********************************************************************//**
 * @brief Void constructor
 ***************************************************************************/
cterror::cterror(void) : ctool(CTERROR_NAME, CTERROR_VERSION)
{
    // Initialise members
    init_members();

    // Return
    return;
}


/***********************************************************************//**
 * @brief Observations constructor
 *
 * param[in] obs Observation container.
 *
 * This method creates an instance of the class by copying an existing
 * observations container.
 ***************************************************************************/
cterror::cterror(const GObservations& obs) :
          ctool(CTERROR_NAME, CTERROR_VERSION)
{
    // Initialise members
    init_members();

    // Set observations
    m_obs = obs;

    // Return
    return;
}



/***********************************************************************//**
 * @brief Command line constructor
 *
 * @param[in] argc Number of arguments in command line.
 * @param[in] argv Array of command line arguments.
 ***************************************************************************/
cterror::cterror(int argc, char *argv[]) :
          ctool(CTERROR_NAME, CTERROR_VERSION, argc, argv)
{
    // Initialise members
    init_members();

    // Return
    return;
}


/***********************************************************************//**
 * @brief Copy constructor
 *
 * @param[in] app Application.
 ***************************************************************************/
cterror::cterror(const cterror& app) : ctool(app)
{
    // Initialise members
    init_members();

    // Copy members
    copy_members(app);

    // Return
    return;
}


/***********************************************************************//**
 * @brief Destructor
 ***************************************************************************/
cterror::~cterror(void)
{
    // Free members
    free_members();

    // Return
    return;
}


/*==========================================================================
 =                                                                         =
 =                               Operators                                 =
 =                                                                         =
 ==========================================================================*/

/***********************************************************************//**
 * @brief Assignment operator
 *
 * @param[in] app Application.
 * @return Application.
 ***************************************************************************/
cterror& cterror::operator=(const cterror& app)
{
    // Execute only if object is not identical
    if (this != &app) {

        // Copy base class members
        this->ctool::operator=(app);

        // Free members
        free_members();

        // Initialise members
        init_members();

        // Copy members
        copy_members(app);

    } // endif: object was not identical

    // Return this object
    return *this;
}


/*==========================================================================
 =                                                                         =
 =                            Public methods                               =
 =                                                                         =
 ==========================================================================*/

/***********************************************************************//**
 * @brief Clear instance
 ***************************************************************************/
void cterror::clear(void)
{
    // Free members
    free_members();
    this->ctool::free_members();
    this->GApplication::free_members();

    // Initialise members
    this->GApplication::init_members();
    this->ctool::init_members();
    init_members();

    // Return
    return;
}


/***********************************************************************//**
 * @brief Computes 
 *
 ***************************************************************************/
void cterror::run(void)
{
    // If we're in debug mode then all output is also dumped on the screen
    if (logDebug()) {
        log.cout(true);
    }

    // Get task parameters
    get_parameters();

    // Write parameters into logger
    if (logTerse()) {
        log_parameters();
        log << std::endl;
    }

    // Write observation(s) into logger
    if (logTerse()) {
        log << std::endl;
        if (m_obs.size() > 1) {
            log.header1("Observations");
        }
        else {
            log.header1("Observation");
        }
        log << m_obs << std::endl;
    }

    // Save original models
    GModels models_orig = m_obs.models();

    // Allocate optimizer
    m_opt = new GOptimizerLM();
    // Optimize and save best log-likelihood
    m_obs.optimize(*m_opt);
    m_obs.errors(*m_opt);
    m_best_logL = m_obs.logL();

    // Write header
    if (logTerse()) {
        log << std::endl;
        log.header1("Compute best-fit likelihood");
    }

    // Write optimised model into logger
    if (logTerse()) {
        log << m_obs.models() << std::endl;
    }


    // Continue only if source model exists
    if (m_obs.models().contains(m_srcname)) {

        GModels& models = const_cast<GModels&>(m_obs.models());
        m_skymodel      = dynamic_cast<GModelSky*>(models[m_srcname]);
        if (m_skymodel == NULL) {
            std::string msg = "Source \""+m_srcname+"\" is not a sky model. "
                    "Please specify the name of a sky model for "
                    "parameter error computation.";
            throw GException::invalid_value(G_RUN, msg);
        }

        int npars = m_skymodel->spectral()->size();


        for (int i = 0; i < npars; ++i)
        {

            // Re-optimize
            m_obs.optimize(*m_opt);

            if(m_skymodel->spectral()->at(i).is_fixed())
                continue;

            m_model_par = &(m_skymodel->spectral()->at(i));

            // Compute parameter bracketing
            m_value  = m_model_par->factor_value();
            double parmin = std::max(m_model_par->factor_min(),
                                     m_value - 10*m_model_par->factor_error());
            double parmax = std::min(m_model_par->factor_max(),
                                     m_value + 10*m_model_par->factor_error());

            // Write header
            if (logTerse()) {
                log << std::endl;
                log.header1("Compute parameter error");
                log << gammalib::parformat("Model name");
                log << m_skymodel->name() << std::endl;
                log << gammalib::parformat("Parameter name");
                log << m_model_par->name() << std::endl;
                log << gammalib::parformat("Confidence level");
                log << m_confidence*100.0 << "%" << std::endl;
                log << gammalib::parformat("Log-likelihood difference");
                log << m_dlogL << std::endl;
                log << gammalib::parformat("Initial parameter range");
                log << "[";
                log << parmin;
                log << ", ";
                log << parmax;
                log << "]" << std::endl;
            }

            // Compute lower boundary
            error_bisection(parmin, m_value);
            double value_lo = m_model_par->factor_value();

            if (logTerse()) {
                log << gammalib::parformat("Final lower parameter value");
                log << value_lo << std::endl;
            }

            // Reset parameter to original value
            m_model_par->factor_value(m_value);

            // Compute upper boundary
            error_bisection(m_value, parmax);
            double value_hi = m_model_par->factor_value();

            if (logTerse()) {
                log << gammalib::parformat("Final upper parameter");
                log << value_hi << std::endl;
            }

            // Reset parameter to original value
            m_model_par->factor_value(m_value);

            // Compute errors
            m_error = 0.5*(value_hi - value_lo);
            double error_max = std::max(value_hi-m_value, m_value-value_lo);
            double error_min = std::min(value_hi-m_value, m_value-value_lo);


            // Write results to logfile
            if (logTerse()) {
                log << std::endl;
                log.header1("Error results");
                log << gammalib::parformat("Max error");
                log << error_max;
                log << gammalib::parformat("Min error");
                log << error_min;
                log << gammalib::parformat("Mean parameter error");
                log << m_error;
                log << " " << m_model_par->unit();
                log << std::endl;
                log << gammalib::parformat("Parameter scale");
                log << m_model_par->scale();
                log << std::endl;
            }

            // Save error result
            m_model_par->factor_error(m_error);

        }

    }


    // Return
    return;
}

/***********************************************************************//**
 * @brief Save maps
 *
 * This method saves the error to an ascii file.
 *
 * @todo No yet implemented as we have no clear use case yet for saving
 * the result.
 ***************************************************************************/
void cterror::save(void)
{
    // Write header
    if (logTerse()) {
        log << std::endl;
        log.header1("Save results");
    }


    // Get output filename
    std::string outmodel = (*this)["outfile"].filename();

     // Write results out as XML model
    if (gammalib::toupper(outmodel) != "NONE") {
        m_obs.models().save(outmodel);
    }

    // Return
    return;
}

/*==========================================================================
 =                                                                         =
 =                             Private methods                             =
 =                                                                         =
 ==========================================================================*/

/***********************************************************************//**
 * @brief Initialise class members
 ***************************************************************************/
void cterror::init_members(void)
{
    // Initialise user parameters
    m_srcname.clear();
    m_confidence = 0.68;
    m_sigma_min  = 0.0;
    m_sigma_max  = 0.0;
    m_tol        = 1.0e-3;
    m_max_iter   = 50;
    m_value      = 0.0;
    m_error      = 0.0;

    // Initialise protected members
    m_obs.clear();
    m_dlogL        = 0.0;
    m_skymodel     = NULL;
    m_model_par    = NULL;
    m_best_logL    = 0.0;

    // Return
    return;
}


/***********************************************************************//**
 * @brief Copy class members
 *
 * @param[in] app Application.
 ***************************************************************************/
void cterror::copy_members(const cterror& app)
{
    // Copy user parameters
    m_srcname    = app.m_srcname;
    m_confidence = app.m_confidence;
    m_sigma_min  = app.m_sigma_min;
    m_sigma_max  = app.m_sigma_max;
    m_tol        = app.m_tol;
    m_max_iter   = app.m_max_iter;

    // Copy protected members
    m_obs          = app.m_obs;
    m_dlogL        = app.m_dlogL;
    m_best_logL    = app.m_best_logL;

    // Return
    return;
}


/***********************************************************************//**
 * @brief Delete class members
 ***************************************************************************/
void cterror::free_members(void)
{
    // Return
    return;
}


/***********************************************************************//**
 * @brief Get application parameters
 *
 * @exception GException::invalid_value
 *            Test source not found.
 *
 * Get all task parameters from parameter file or (if required) by querying
 * the user.
 ***************************************************************************/
void cterror::get_parameters(void)
{
    // If there are no observations in container then load them via user
    // parameters
    if (m_obs.size() == 0) {

        // Throw exception if no input observation file is given
        require_inobs(G_GET_PARAMETERS);

        // Build observation container
        m_obs = get_observations();

    } // endif: there was no observation in the container


    // If there are no models associated with the observations then
    // load now the model definition
    if (m_obs.models().size() == 0) {

        // Get models XML filename
        std::string filename = (*this)["inmodel"].filename();

        // Setup models for optimizing.
        m_obs.models(GModels(filename));

    } // endif: no models were associated with observations

    // Get name of test source and check container for this name
    m_srcname = (*this)["srcname"].string();
    if (!m_obs.models().contains(m_srcname)) {
        std::string msg = "Source \""+m_srcname+"\" not found in model "
                          "container. Please add a source with that name "
                          "or check for possible typos.";
        throw GException::invalid_value(G_GET_PARAMETERS, msg);
    }

    // Get confidence level and transform into log-likelihood difference
    m_confidence = (*this)["confidence"].real();

    double sigma = gammalib::erfinv(m_confidence) * gammalib::sqrt_two;
    m_dlogL      = (sigma*sigma) / 2.0;

    // Read starting boundaries for bisection
    m_sigma_min = (*this)["sigma_min"].real();
    m_sigma_max = (*this)["sigma_max"].real();

    // Read precision
    m_tol      = (*this)["tol"].real();
    m_max_iter = (*this)["max_iter"].integer();


    // Return
    return;
}


/***********************************************************************//**
 * @brief Performs error computation by using a bisection method
 *
 * @param[in] min Minimum parameter value
 * @param[in] max Maximum parameter value
 *
 * This method calculates the error using a bisection method.
 ***************************************************************************/
void cterror::error_bisection(const double& min, const double& max)
{
    // Copy values to working values
    double wrk_min = min;
    double wrk_max = max;

    // Initialise iteration counter
    int iter = 0;

    // Loop until breaking condition is reached
    while (true) {

        // Log information
        if (logExplicit()) {
            log << gammalib::parformat("Iteration "+gammalib::str(iter));
            log << "[";
            log << wrk_min;
            log << ", ";
            log << wrk_max;
            log << "]" << std::endl;
        }

        // Throw exception if maximum iterations are reached
        if (iter > m_max_iter) {
            if(wrk_min - m_model_par->factor_min() < m_tol)
            {
                std::string msg = "The "+m_model_par->name()+" parameter minimum has been"
                                  " reached during error calculation. To obtain accurate "
                                  " errors, consider to set the minimum to a lower value,"
                                  " and re-run cterror.";
                if (logTerse()) {
                    log << msg;
                }
                break;
            }
            else if(m_model_par->factor_max() - wrk_max < m_tol)
            {
                std::string msg = "The "+m_model_par->name()+" parameter maximum has been"
                                  " reached during error calculation. To obtain accurate "
                                  " errors, consider to set the maxmimum to a higher value"
                                  ", and re-run cterror.";
                if (logTerse()) {
                    log << msg;
                }
                break;
            }
            else
            {
                std::string msg = "The maximum number of "+gammalib::str(m_max_iter)+
                                  " has been reached. You may consider to increase"
                                  " the \"max_iter\" parameter, and re-run cterror.";
                throw GException::invalid_value(G_ERR_BISECTION, msg);
            }
        }

        // Compute center of boundary
        double mid = (wrk_min + wrk_max) / 2.0;

        // Calculate function value
        double eval_mid = evaluate(mid);

        // Check for convergence inside tolerance
        if (std::abs(eval_mid) < m_tol) {
            break;
        }

        // If we are on the crescent side of the parabola
        if (mid > m_value)
        {
            // Change boundaries for further iteration
            if (eval_mid > 0.0) {
                wrk_max = mid;
            }
            else if (eval_mid < 0.0) {
                wrk_min = mid;
            }
        }
        // If we are on the decrescent side of the parabola
        else
        {
            // Change boundaries for further iteration
            if (eval_mid > 0.0) {
                wrk_min = mid;
            }
            else if (eval_mid < 0.0) {
                wrk_max = mid;
            }
        }

        // Increment counter
        iter++;

    } // endwhile

    // Return
    return;

}


/***********************************************************************//**
 * @brief Evaluates the log-likelihood
 *
 * @param[in] value Parameter factor value
 * @return Log-likelihood value
 *
 * This method evaluates the log-likelihood as a function of the parameter
 * of interest.
 ***************************************************************************/
double cterror::evaluate(const double& value)
{
    // Initialise log-likelihood value
    double logL = 0.0;

    // Check if given parameter is within boundaries
    if (value > m_model_par->factor_min() && value < m_model_par->factor_max()) {

        // Change parameter factor
        m_model_par->factor_value(value);

        //Fix parameter
        m_model_par->fix();

        // Re-optimize
        m_obs.optimize(*m_opt);

        // Evaluate likelihood for new model container
        m_obs.eval();

        // Retrieve likelihood
        logL = m_obs.logL();

        // Free parameter
        m_model_par->free();

    } // endif: value was inside allowed range

    // ... otherwise signal that the parameter went outside the boundaries
    else {
        std::string msg = "Value of parameter \""+m_model_par->name()+"\" "
                          "outside of validity range requested. To omit "
                          "this error please enlarge the  parameter range "
                          "in the model XML file.";
        throw GException::invalid_value(G_EVALUATE, msg);
    }

    // Compute function value
    double logL_difference = logL - m_best_logL - m_dlogL;


    // Return
    return logL_difference;
}